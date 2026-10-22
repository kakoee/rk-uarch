//! Byte-segment lifetime validation, independent of the mapper. No timing execution.
use super::*;
type Access = (String, u64, u64);
fn range(v: &Value) -> Result<Access> {
    Ok((
        t(&v["buffer_id"]).into(),
        n(&v["offset_bytes"]),
        add(n(&v["offset_bytes"]), n(&v["size_bytes"]))?,
    ))
}
fn accesses(j: &Value) -> Result<(Vec<Access>, Vec<Access>)> {
    let mut reads = vec![];
    let mut writes = vec![];
    match t(&j["kind"]) {
        "dma" => {
            for span in a(&j["spans"]) {
                let size = n(&span["payload_bytes"]);
                let so = n(&span["source_offset_bytes"]);
                let dest = n(&span["destination_offset_bytes"]);
                reads.push((t(&j["source"]["buffer_id"]).into(), so, add(so, size)?));
                writes.push((
                    t(&j["destination"]["buffer_id"]).into(),
                    dest,
                    add(dest, size)?,
                ));
            }
        }
        "local_transfer" => {
            reads.push(range(&j["source"])?);
            writes.push(range(&j["destination"])?);
        }
        "vector" => {
            for x in a(&j["inputs"]) {
                reads.push(range(x)?);
            }
            for x in a(&j["outputs"]) {
                writes.push(range(x)?);
            }
        }
        "compute" => {
            let d = &j["tile_extents"];
            let width = if j["operand_dtypes"]["X"] == "int8" {
                1
            } else {
                2
            };
            reads.push((
                t(&j["operand_buffers"]["X"]).into(),
                0,
                mul(mul(n(&d["M"]), n(&d["K"]))?, width)?,
            ));
            reads.push((
                t(&j["operand_buffers"]["W"]).into(),
                0,
                mul(mul(n(&d["K"]), n(&d["N"]))?, width)?,
            ));
            let partial = (
                t(&j["accumulator_buffer_id"]).into(),
                0,
                mul(mul(n(&d["M"]), n(&d["N"]))?, 4)?,
            );
            if n(&j["tile_origin"]["K"]) > 0 {
                reads.push(partial.clone());
            }
            writes.push(partial);
        }
        _ => {}
    }
    Ok((reads, writes))
}
fn precedes(a: usize, b: usize, ancestors: &[Vec<(usize, usize)>], rank: &[usize]) -> bool {
    let intervals = &ancestors[b];
    let at = intervals.partition_point(|&(lo, _)| lo <= rank[a]);
    at > 0 && rank[a] <= intervals[at - 1].1
}
pub(super) fn validate(g: &Value) -> Result<()> {
    let jobs = a(&g["jobs"]);
    let ids: BTreeMap<_, _> = jobs
        .iter()
        .enumerate()
        .map(|(i, j)| (t(&j["id"]), i))
        .collect();
    let buffers: BTreeMap<_, _> = a(&g["buffers"])
        .iter()
        .map(|b| (t(&b["id"]).to_owned(), b))
        .collect();
    let mut before = vec![vec![]; jobs.len()];
    let mut after = before.clone();
    let mut degree = vec![0usize; jobs.len()];
    for edge in a(&g["dependencies"]) {
        let left = *ids
            .get(t(&edge["before"]))
            .ok_or_else(|| refuse("InvalidDependency", "", "before"))?;
        let right = *ids
            .get(t(&edge["after"]))
            .ok_or_else(|| refuse("InvalidDependency", "", "after"))?;
        before[right].push(left);
        after[left].push(right);
        degree[right] += 1;
    }
    let mut queue: VecDeque<_> = degree
        .iter()
        .enumerate()
        .filter(|(_, d)| **d == 0)
        .map(|(i, _)| i)
        .collect();
    let mut order = vec![];
    while let Some(j) = queue.pop_front() {
        order.push(j);
        for &next in &after[j] {
            degree[next] -= 1;
            if degree[next] == 0 {
                queue.push_back(next);
            }
        }
    }
    require(order.len() == jobs.len(), "InvalidDependency", "cycle")?;
    let mut rank = vec![0; order.len()];
    for (i, &j) in order.iter().enumerate() {
        rank[j] = i;
    }
    let mut ancestors: Vec<Vec<(usize, usize)>> = vec![vec![]; jobs.len()];
    for &j in &order {
        let mut spans = vec![(rank[j], rank[j])];
        for &p in &before[j] {
            spans.extend_from_slice(&ancestors[p]);
        }
        spans.sort_unstable();
        let mut merged: Vec<(usize, usize)> = vec![];
        for (lo, hi) in spans {
            if let Some(last) = merged.last_mut()
                && lo <= last.1 + 1
            {
                last.1 = last.1.max(hi);
            } else {
                merged.push((lo, hi));
            }
        }
        ancestors[j] = merged;
    }
    let uses = jobs.iter().map(accesses).collect::<Result<Vec<_>>>()?;
    let mut bounds: BTreeMap<String, BTreeSet<u64>> = BTreeMap::new();
    for (read, write) in &uses {
        for (name, lo, hi) in read.iter().chain(write) {
            let buffer = buffers
                .get(name)
                .ok_or_else(|| refuse("InvalidResource", "", "access buffer"))?;
            require(
                lo < hi && *hi <= n(&buffer["size_bytes"]),
                "InvalidResource",
                "access bounds",
            )?;
            bounds.entry(name.clone()).or_default().extend([*lo, *hi]);
        }
    }
    let points: BTreeMap<_, Vec<_>> = bounds
        .into_iter()
        .map(|(name, b)| (name, b.into_iter().collect()))
        .collect();
    type State = Vec<(Option<usize>, BTreeSet<usize>)>;
    let mut state: BTreeMap<String, State> = points
        .iter()
        .map(|(name, p)| (name.clone(), vec![(None, BTreeSet::new()); p.len() - 1]))
        .collect();
    for j in order {
        for (writing, spans) in [(false, &uses[j].0), (true, &uses[j].1)] {
            for (name, lo, hi) in spans {
                let p = &points[name];
                let from = p.binary_search(lo).unwrap();
                let to = p.binary_search(hi).unwrap();
                for segment in &mut state.get_mut(name).unwrap()[from..to] {
                    if let Some(writer) = segment.0 {
                        require(
                            precedes(writer, j, &ancestors, &rank),
                            "InvalidDependency",
                            "buffer producer",
                        )?;
                    } else if !writing {
                        require(
                            buffers[name]["initial_residency"] == "preloaded",
                            "InvalidResource",
                            "uninitialized read",
                        )?;
                    }
                    if writing {
                        require(
                            segment.1.iter().all(|&r| precedes(r, j, &ancestors, &rank)),
                            "LiveBufferAlias",
                            "write before readers",
                        )?;
                        *segment = (Some(j), BTreeSet::new());
                    } else {
                        segment.1.insert(j);
                    }
                }
            }
        }
    }
    let mut written: BTreeMap<String, Vec<(u64, u64)>> = BTreeMap::new();
    for (_, writes) in &uses {
        for (name, lo, hi) in writes {
            written.entry(name.clone()).or_default().push((*lo, *hi));
        }
    }
    for (name, b) in &buffers {
        if b["space"] == "vmem" {
            require(
                b["initial_residency"] == "uninitialized",
                "UnsupportedInitialState",
                "VMEM reload",
            )?;
        }
        if b["space"] == "hbm"
            && matches!(b["operand"].as_str(), Some("Y" | "O" | "K_out" | "V_out"))
        {
            require(
                b["initial_residency"] == "uninitialized",
                "InvalidResource",
                "preloaded output",
            )?;
        }
        if b["space"] == "hbm" && b["initial_residency"] == "uninitialized" {
            let spans = written.entry(name.clone()).or_default();
            spans.sort_unstable();
            let mut cursor = 0;
            for &(lo, hi) in spans.iter() {
                require(lo <= cursor, "MissingCoverage", "output hole")?;
                cursor = cursor.max(hi);
            }
            require(
                cursor == n(&b["size_bytes"]),
                "MissingCoverage",
                "output store",
            )?;
        }
    }
    Ok(())
}
