//! Model-3 service policy for the existing Runtime, sequences, activities and wheel.
use super::*;
type Key = (u64, u64, String, usize);
#[derive(Default)]
pub(super) struct ReferenceState {
    pub pending: BTreeSet<Key>,
    runnable: BTreeSet<Key>,
    successors: Vec<Vec<usize>>,
    remaining: Vec<usize>,
    ready: BTreeSet<usize>,
    predecessors: Vec<Vec<usize>>,
    pub issue_next: u64,
    released: Option<usize>,
    pub completed: usize,
    starts: Vec<Vec<usize>>,
    ends: Vec<Vec<usize>>,
    buffer_remaining: Vec<usize>,
    pub metadata_before: BTreeSet<String>,
    pub metadata_after: BTreeSet<String>,
    last_issue: Option<usize>,
    issue_causes: BTreeMap<usize, Vec<(usize, &'static str)>>,
}
impl Runtime {
    pub(super) fn new_reference(v: &Admitted) -> Result<Self> {
        let mut rs = ReferenceState {
            successors: vec![vec![]; v.graph.jobs.len()],
            predecessors: vec![vec![]; v.graph.jobs.len()],
            remaining: vec![0; v.graph.jobs.len()],
            starts: vec![vec![]; v.graph.jobs.len()],
            ends: vec![vec![]; v.graph.jobs.len()],
            buffer_remaining: v.graph.buffers.iter().map(|b| b.consumers.len()).collect(),
            ..ReferenceState::default()
        };
        for (i, b) in v.graph.buffers.iter().enumerate() {
            if let Some(j) = b.producer {
                rs.starts[j].push(i);
            }
            if !b.persistent {
                for &j in &b.consumers {
                    rs.ends[j].push(i);
                }
            }
        }
        for &(a, b) in &v.graph.dependencies {
            rs.successors[a].push(b);
            rs.predecessors[b].push(a);
            rs.remaining[b] += 1;
        }
        for j in 0..rs.remaining.len() {
            if rs.remaining[j] == 0 {
                rs.ready.insert(j);
            }
        }
        let mut r =
            Self {
                observations: ObservationVersion::V4,
                reservation_opportunities: vec![],
                eligibility_dirty: false,
                pending_issue: BTreeMap::new(),
                allocations:
                    v.graph
                        .buffers
                        .iter()
                        .enumerate()
                        .map(|(i, b)| Allocation {
                            start: if b.persistent
                                || v.raw["workload_closure"]["points"][0]["task_graph"]["buffers"]
                                    [i]["initial_residency"]
                                    == "preloaded"
                            {
                                Some(0)
                            } else {
                                None
                            },
                            end: None,
                        })
                        .collect(),
                activities: vec![],
                events: vec![],
                sequences: vec![],
                jobs: vec![JobState::default(); v.graph.jobs.len()],
                counts: Counts::default(),
                per_job: vec![Counts::default(); v.graph.jobs.len()],
                duration: 0,
                max_live_events: 0,
                wheel: Wheel::with_bucket_width_ps(1000).map_err(|_| overflow())?,
                pending_count: 0,
                busy: BTreeMap::new(),
                last: BTreeMap::new(),
                channels: BTreeMap::new(),
                inflight: BTreeMap::new(),
                now: 0,
                reference_state: Some(rs),
            };
        for (job, t) in v.graph.jobs.iter().enumerate() {
            let TaskKind::Reference { sequences } = &t.kind else {
                return Err(refuse("InternalError", "", "reference task"));
            };
            for (index, rs) in sequences.iter().enumerate() {
                let s = Sequence {
                    job,
                    request: Some(format!("{}:{index:08}", t.id)),
                    engine: if rs.hbm { Some(0) } else { None },
                    source: None,
                    destination: None,
                    payload: rs.bytes,
                    write: rs.write,
                    route: None,
                    phases: rs.phases.clone(),
                    step: 0,
                    ready: 0,
                    reservation: None,
                    issue: None,
                    end: None,
                    activities: vec![],
                    active: false,
                    service_ready: false,
                    enabled: false,
                    credit_causes: vec![],
                };
                r.jobs[job].sequences.push(r.sequences.len());
                r.sequences.push(s);
            }
        }
        Ok(r)
    }
    fn reference_key(&self, s: usize) -> Key {
        let seq = &self.sequences[s];
        (
            seq.ready,
            seq.engine.unwrap_or(0),
            seq.request.clone().unwrap(),
            s,
        )
    }
    pub(super) fn reference_queue(&mut self, s: usize) {
        if self.reference_state.is_some() {
            let key = self.reference_key(s);
            let Some(state) = &mut self.reference_state else {
                return;
            };
            if self.sequences[s].engine.is_some()
                && self.sequences[s].issue.is_none()
                && self.sequences[s].phases[self.sequences[s].step].name == "r_latency"
            {
                state.pending.insert(key);
            } else {
                state.runnable.insert(key);
            }
        }
    }
    pub(super) fn reference_dequeue(&mut self, s: usize) {
        if self.reference_state.is_some() {
            let key = self.reference_key(s);
            if let Some(state) = &mut self.reference_state {
                state.runnable.remove(&key);
            }
        }
    }
    pub(super) fn reference_set_metadata(&mut self, metadata: BTreeSet<String>) {
        let r = self.reference_state.as_mut().unwrap();
        r.metadata_before = metadata.clone();
        r.metadata_after = metadata;
    }
    pub(crate) fn reference_metadata(&self) -> (&BTreeSet<String>, &BTreeSet<String>) {
        let r = self.reference_state.as_ref().unwrap();
        (&r.metadata_before, &r.metadata_after)
    }
    pub(super) fn reference_alloc_start(&mut self, j: usize) -> bool {
        if let Some(r) = &self.reference_state {
            for &i in &r.starts[j] {
                self.allocations[i].start.get_or_insert(self.now);
            }
            true
        } else {
            false
        }
    }
    pub(super) fn reference_alloc_end(&mut self, _v: &Admitted, j: usize) -> bool {
        if let Some(r) = &mut self.reference_state {
            for &i in &r.ends[j] {
                r.buffer_remaining[i] -= 1;
                if r.buffer_remaining[i] == 0 {
                    self.allocations[i].end.get_or_insert(self.now);
                }
            }
            true
        } else {
            false
        }
    }
    pub(super) fn reference_issue_causes(&self, s: usize) -> Vec<(usize, &'static str)> {
        if self.sequences[s].phases[self.sequences[s].step].name == "r_latency" {
            self.reference_state
                .as_ref()
                .and_then(|r| r.issue_causes.get(&s))
                .cloned()
                .unwrap_or_default()
        } else {
            vec![]
        }
    }
    pub(super) fn reference_predecessors(&self, j: usize) -> Option<&Vec<usize>> {
        self.reference_state.as_ref().map(|r| &r.predecessors[j])
    }
    pub(super) fn reference_runnable(&self) -> Vec<Key> {
        self.reference_state
            .as_ref()
            .unwrap()
            .runnable
            .iter()
            .cloned()
            .collect()
    }
    pub(super) fn reference_complete(&mut self, v: &Admitted, j: usize) {
        if let Some(r) = &mut self.reference_state {
            r.completed += 1;
            if v.graph.jobs[j].raw["kind"] == "control" {
                for buffer in &v.graph.buffers {
                    if buffer.persistent && buffer.producer == Some(j) {
                        r.metadata_after.insert(buffer.id.clone());
                    }
                }
            }
            for &next in &r.successors[j] {
                r.remaining[next] -= 1;
                if r.remaining[next] == 0 {
                    r.ready.insert(next);
                }
            }
        }
    }
    pub(super) fn reference_ready(&mut self, _v: &Admitted) {
        let ready = std::mem::take(&mut self.reference_state.as_mut().unwrap().ready);
        for j in ready {
            let t = self.reference_state.as_ref().unwrap().predecessors[j]
                .iter()
                .map(|&i| self.jobs[i].end.unwrap())
                .max()
                .unwrap_or(0);
            self.jobs[j].ready = Some(t);
            for s in self.jobs[j].sequences.clone() {
                self.sequences[s].enabled = true;
                self.sequences[s].ready = t;
                if self.sequences[s].engine.is_some() && !self.sequences[s].write {
                    let key = self.reference_key(s);
                    self.reference_state.as_mut().unwrap().pending.insert(key);
                } else {
                    if self.sequences[s].engine.is_none() {
                        self.sequences[s].issue = Some(t);
                    }
                    self.reference_queue(s);
                }
            }
        }
    }
    pub(super) fn reference_issue(&mut self, v: &Admitted) -> Result<bool> {
        let h = v.reference.as_ref().unwrap();
        if self.reference_state.as_ref().unwrap().issue_next > self.now
            || self.inflight.get(&0).map_or(0, BTreeSet::len) >= h.window as usize
        {
            return Ok(false);
        }
        let Some(key) = self
            .reference_state
            .as_ref()
            .unwrap()
            .pending
            .first()
            .cloned()
        else {
            return Ok(false);
        };
        if key.0 > self.now {
            return Ok(false);
        }
        self.reference_state.as_mut().unwrap().pending.remove(&key);
        let s = key.3;
        let credit_wait = self.now > key.0.max(self.reference_state.as_ref().unwrap().issue_next);
        if let Some(a) = self.reference_state.as_ref().unwrap().released
            && self.activities[a].end == self.now
            && credit_wait
        {
            self.sequences[s].credit_causes.push(a);
        }
        let mut causes = vec![];
        if self.now == self.reference_state.as_ref().unwrap().issue_next
            && let Some(previous) = self.reference_state.as_ref().unwrap().last_issue
            && let Some(&activity) = self.sequences[previous]
                .activities
                .iter()
                .find(|&&a| self.activities[a].phase.name == "r_latency")
        {
            causes.push((activity, "issue_spacing"));
        }
        if let Some(a) = self.reference_state.as_ref().unwrap().released
            && self.activities[a].end == self.now
            && credit_wait
        {
            causes.push((a, "credit"));
        }
        self.reference_state
            .as_mut()
            .unwrap()
            .issue_causes
            .insert(s, causes);
        self.reference_state.as_mut().unwrap().last_issue = Some(s);
        self.sequences[s].issue = Some(self.now);
        self.sequences[s].ready = self.now;
        self.reference_state.as_mut().unwrap().issue_next =
            add(self.now, h.p("hbm_issue_interval_ps")?.ceil()?)?;
        self.inflight.entry(0).or_default().insert(s);
        self.reference_queue(s);
        Ok(true)
    }
    pub(super) fn reference_release(&mut self, s: usize, a: usize) {
        self.inflight.entry(0).or_default().remove(&s);
        self.reference_state.as_mut().unwrap().released = Some(a);
    }
    pub(super) fn reference_service(
        &mut self,
        _s: usize,
        p: &Phase,
        ready: u64,
    ) -> Result<(u64, Option<(Ratio, Ratio)>)> {
        let service = p.service.unwrap();
        let lo = if p.name == "r_hbm" || p.name == "r_vmem" {
            self.channels
                .get(&p.owner)
                .copied()
                .unwrap_or(Ratio::integer(0))
                .max_integer(ready)?
        } else {
            Ratio::integer(self.now)
        };
        let hi = lo.plus(service)?;
        if p.name == "r_hbm" || p.name == "r_vmem" {
            self.channels.insert(p.owner, hi);
        }
        Ok((hi.ceil()?, Some((lo, hi))))
    }
}
