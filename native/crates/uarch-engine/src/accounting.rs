//! Measured fixed-delay observations; historical K1 predecessors are not blockers.
use crate::admission::Validated;
use crate::carrier::{Result, refuse};
use crate::hardware;
use crate::{Action, Delay, Error, Kind, Outcome, next_edge};
use serde_json::{Value, json};
fn observed(records: Vec<Value>) -> Value {
    json!({"status":"observed","records":records})
}
fn unrepresented() -> Value {
    json!({"status":"unrepresented","reason":"fixed_delay/1 does not represent this activity"})
}
fn kind(k: u16) -> Result<&'static str> {
    for (value, name) in [
        (Kind::TaskReady, "TASK_READY"),
        (Kind::ComputeDone, "COMPUTE_DONE"),
        (Kind::DependencyReady, "DEPENDENCY_READY"),
        (Kind::OwnerGrant, "OWNER_GRANT"),
        (Kind::TaskRelease, "TASK_RELEASE"),
    ] {
        if k == value as u16 {
            return Ok(name);
        }
    }
    Err(refuse(
        "InternalError",
        "",
        "unexpected observed event kind",
    ))
}
pub(crate) fn construct(v: &Validated, out: &Outcome) -> Result<Value> {
    let mut events = Vec::new();
    let mut complete_order = vec![0; v.jobs.len()];
    let mut grant_order = vec![0; v.jobs.len()];
    for r in out.records.iter().filter(|r| r.action == Action::Dispatch) {
        let ordinal = events.len() as u64;
        if r.event_kind == Kind::ComputeDone as u16 {
            complete_order[r.job_id as usize] = ordinal;
        }
        if r.event_kind == Kind::OwnerGrant as u16 {
            grant_order[r.job_id as usize] = ordinal;
        }
        events.push(json!({"event_seq":r.event_seq,"observation_ordinal":ordinal,"t_ps":r.t_ps,"phase":r.phase,"target_id":v.owner_ids[r.owner as usize],"kind":kind(r.event_kind)?,"job_id":v.job_ids[r.job_id as usize]}));
    }
    let mut jobs = Vec::new();
    let mut intervals = Vec::new();
    let mut queues = Vec::new();
    let mut clocks = Vec::new();
    let mut chosen = Vec::new();
    let mut busy = vec![0u64; v.owner_ids.len()];
    for (i, j) in out.jobs.iter().enumerate() {
        let tight: Vec<_> = j
            .dependency_resource_predecessors
            .iter()
            .copied()
            .filter(|p| {
                out.jobs[*p as usize].end_ps == j.start_ps
                    && complete_order[*p as usize] < grant_order[i]
            })
            .collect();
        chosen.push(tight.first().copied());
        let owner = v.owner_ids[j.owner as usize];
        let id = &v.job_ids[i];
        jobs.push(json!({"job_id":id,"op_id":null,"group_id":null,"repeat_index":null,"tile_origin":null,"tile_extents":null,"release_ps":j.release_ps,"ready_ps":j.ready_ps,"start_ps":j.start_ps,"end_ps":j.end_ps,"owner_id":owner,"blocking_predecessor_ids":tight.iter().map(|p|v.job_ids[*p as usize].clone()).collect::<Vec<_>>(),"useful_matrix_ops":0,"issued_matrix_ops":0,"vector_arithmetic_ops":0,"cast_ops":0}));
        for (population, enter, leave) in [
            ("waiting", j.ready_ps, j.start_ps),
            ("service", j.start_ps, j.end_ps),
        ] {
            queues.push(json!({"queue_id":format!("owner:{owner}:{population}"),"item_id":id,"population":population,"enter_ps":enter,"leave_ps":leave,"owner_id":owner,"clock_domain":null}));
        }
        if j.end_ps > j.start_ps {
            intervals.push(json!({"owner_id":owner,"job_id":id,"start_ps":j.start_ps,"end_ps":j.end_ps,"activity":"fixed_delay","limiting_resource_id":owner,"service_start_ps_ratio":null,"service_end_ps_ratio":null}));
            busy[j.owner as usize] = busy[j.owner as usize]
                .checked_add(j.end_ps - j.start_ps)
                .ok_or_else(|| refuse("InternalError", "", "busy interval overflow"))?;
        }
        if let Delay::Cycles { domain, n_cycles } = v.jobs[i].duration {
            let raw = next_edge(v.clocks[domain], j.start_ps, 0);
            let (status, aligned) = match raw {
                Ok(t) => ("success", Some(t)),
                Err(Error::TimeOverflow) => ("TimeOverflow", None),
                Err(_) => return Err(refuse("InternalError", "", "raw clock failure")),
            };
            clocks.push(json!({"job_id":id,"domain":(["core","noc","dram"][domain]),"grant_ps":j.start_ps,"n_cycles":n_cycles,"raw_edge_outcome":status,"aligned_start_ps":aligned,"completion_ps":j.end_ps}));
        }
    }
    intervals.sort_by(|a, b| {
        a["owner_id"]
            .as_u64()
            .cmp(&b["owner_id"].as_u64())
            .then(a["job_id"].as_str().cmp(&b["job_id"].as_str()))
    });
    queues.sort_by(|a, b| {
        a["queue_id"]
            .as_str()
            .cmp(&b["queue_id"].as_str())
            .then(a["item_id"].as_str().cmp(&b["item_id"].as_str()))
            .then(a["population"].as_str().cmp(&b["population"].as_str()))
    });
    let mut critical = Vec::new();
    let mut cursor = out
        .jobs
        .iter()
        .enumerate()
        .min_by(|(a, x), (b, y)| {
            y.end_ps
                .cmp(&x.end_ps)
                .then(v.job_ids[*a].cmp(&v.job_ids[*b]))
                .then(x.owner.cmp(&y.owner))
        })
        .map(|(i, _)| i)
        .ok_or_else(|| refuse("InternalError", "", "empty measured jobs"))?;
    let mut seen = vec![false; out.jobs.len()];
    loop {
        if seen[cursor] {
            return Err(refuse("InternalError", "", "causal cycle"));
        }
        seen[cursor] = true;
        let j = &out.jobs[cursor];
        let pred = chosen[cursor];
        if j.start_ps < j.end_ps {
            critical.push(json!({"kind":"service","start_ps":j.start_ps,"end_ps":j.end_ps,"cause_job_id":v.job_ids[cursor],"predecessor_id":pred.map(|p|v.job_ids[p as usize].clone()),"limiting_resource_id":v.owner_ids[j.owner as usize],"category":"overhead"}));
        }
        if let Some(p) = pred {
            cursor = p as usize;
        } else {
            if j.start_ps != j.release_ps {
                return Err(refuse("InternalError", "", "noncausal root"));
            }
            if j.release_ps > 0 {
                critical.push(json!({"kind":"release_idle","start_ps":0,"end_ps":j.release_ps,"cause_job_id":v.job_ids[cursor],"predecessor_id":null,"limiting_resource_id":null,"category":"overhead"}));
            }
            break;
        }
    }
    critical.reverse();
    let observations = json!({"format":"uarch-native-observations/1","events":observed(events.clone()),"jobs":observed(jobs),"clocks":observed(clocks),"dma":unrepresented(),"transfers":unrepresented(),"allocations":unrepresented(),"queue_membership":observed(queues),"resource_intervals":observed(intervals),"critical_path":observed(critical)});
    let mut result = json!({"protocol":"uarch-engine/3","job_hash":v.raw["job_hash"],"engine":v.raw["engine"],"scope":"kernel_fixture","completion":"complete","duration_ps":out.duration_ps,"completed_jobs":v.job_ids,"admission":v.raw["admission"],
        "counts":{"matrix_ops":0.0,"vector_ops":0.0,"memory_read_bytes":0.0,"memory_write_bytes":0.0},
        "ext_counts":{"sram_read_bytes":0.0,"sram_write_bytes":0.0,"noc_flit_hop_count":null},
        "work_counts":{"format":"uarch-native-work-counts/1","completed_mac_count":0,"issued_matrix_ops":0,"vector_arithmetic_ops":0,"cast_ops":0},
        "traffic_counts":{"format":"uarch-native-traffic-counts/1","read_payload_bytes":0,"write_payload_bytes":0,"read_transaction_bytes":0,"write_transaction_bytes":0,"unicast_payload_bytes":0},
        "per_op":[],"busy_time_ps":v.owner_ids.iter().zip(busy).map(|(id,n)|json!({"owner_id":id,"busy_time_ps":n})).collect::<Vec<_>>(),
        "attribution_ps":{"compute":0,"memory":0,"noc":0,"sync":0,"overhead":out.duration_ps},
        "diagnostics":{"matrix_util_ratio":null,"vector_util_ratio":null,"dma_compute_overlap_ratio":null,"sram_bank_conflict_stall_ratio":null,"noc_latency_p50_ps":null,"noc_latency_p99_ps":null,"noc_max_link_util_ratio":null,"dram_bw_util_ratio":null,"dram_row_hit_ratio":null,"energy_pj":null},
        "fidelity_detail":null,"unrepresented":["allocations","dma","transfers"],"simulator_metrics":{"event_count":events.len(),"completed_job_count":out.completed_jobs,"max_live_events":out.max_live_events},"trace_hash":null,"u_c0_duration_ps":null,"observations":observations,"owners":v.raw["owners"]});
    result["result_hash"] = Value::String(hardware::digest(&result)?);
    Ok(result)
}
#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Job, Simulation};
    fn private_context(jobs: Vec<Job>, releases: Vec<(u32, u64)>) -> Validated {
        // Accounting helper only: deliberately not a public carrier or authority.
        let job_ids = (0..jobs.len()).map(|i| format!("j{i}")).collect();
        Validated {
            raw: json!({}),
            jobs,
            releases,
            clocks: vec![1_200_000_000],
            owner_ids: vec![7],
            job_ids,
        }
    }
    #[test]
    fn release_idle_is_not_busy_and_zero_history_is_not_a_blocker() {
        let v = private_context(
            vec![
                Job {
                    id: 0,
                    owner: 0,
                    duration: Delay::Picoseconds(3),
                    dependencies: vec![],
                },
                Job {
                    id: 1,
                    owner: 0,
                    duration: Delay::Cycles {
                        domain: 0,
                        n_cycles: 0,
                    },
                    dependencies: vec![],
                },
            ],
            vec![(1, 835)],
        );
        let out =
            Simulation::with_releases(v.clocks.clone(), 1, v.jobs.clone(), v.releases.clone())
                .unwrap()
                .run()
                .unwrap();
        let r = construct(&v, &out).unwrap();
        assert_eq!(r["duration_ps"], 835);
        assert_eq!(r["busy_time_ps"][0]["busy_time_ps"], 3);
        assert_eq!(
            r["observations"]["jobs"]["records"][1]["blocking_predecessor_ids"],
            json!([])
        );
        assert_eq!(
            r["observations"]["critical_path"]["records"][0]["kind"],
            "release_idle"
        );
        assert_eq!(
            r["observations"]["clocks"]["records"][0]["aligned_start_ps"],
            1667
        );
        assert_eq!(
            r["observations"]["clocks"]["records"][0]["completion_ps"],
            835
        );
    }
    #[test]
    fn all_zero_keeps_event_and_queue_inventory_without_busy_or_critical_time() {
        let v = private_context(
            vec![Job {
                id: 0,
                owner: 0,
                duration: Delay::Picoseconds(0),
                dependencies: vec![],
            }],
            vec![],
        );
        let out =
            Simulation::with_releases(v.clocks.clone(), 1, v.jobs.clone(), v.releases.clone())
                .unwrap()
                .run()
                .unwrap();
        let r = construct(&v, &out).unwrap();
        assert_eq!(r["observations"]["critical_path"]["records"], json!([]));
        assert_eq!(
            r["observations"]["resource_intervals"]["records"],
            json!([])
        );
        assert_eq!(
            r["observations"]["queue_membership"]["records"]
                .as_array()
                .unwrap()
                .len(),
            2
        );
        assert_eq!(r["simulator_metrics"]["event_count"], 3);
        assert_eq!(r["simulator_metrics"]["max_live_events"], 1);
    }
}

#[cfg(test)]
mod release_witnesses {
    use super::*;
    use crate::{Job, Simulation};
    #[test]
    fn seventeen_independent_release_witnesses_on_private_mechanics() {
        let cases: Value =
            serde_json::from_str(include_str!("../testdata/private-release-witnesses.json"))
                .unwrap();
        assert_eq!(cases.as_object().unwrap().len(), 17);
        for (case, expected) in cases.as_object().unwrap() {
            let rows = expected["jobs"].as_array().unwrap();
            let ids: Vec<_> = rows
                .iter()
                .map(|r| r[0].as_str().unwrap().to_owned())
                .collect();
            assert!(ids.windows(2).all(|p| p[0] < p[1]));
            let owner_count =
                rows.iter().map(|r| r[1].as_u64().unwrap()).max().unwrap() as usize + 1;
            let mut jobs = Vec::new();
            let mut releases = Vec::new();
            for (i, row) in rows.iter().enumerate() {
                let duration = if let Some(cycles) = row[8].as_u64() {
                    Delay::Cycles {
                        domain: 0,
                        n_cycles: cycles,
                    }
                } else {
                    Delay::Picoseconds(row[7].as_u64().unwrap())
                };
                jobs.push(Job {
                    id: i as u32,
                    owner: row[1].as_u64().unwrap() as u32,
                    duration,
                    dependencies: row[3]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|p| ids.iter().position(|x| x == p.as_str().unwrap()).unwrap() as u32)
                        .collect(),
                });
                releases.push((i as u32, row[2].as_u64().unwrap()));
            }
            // Explicit private mechanics input, no public mapped DTO/authority.
            let v = Validated {
                raw: json!({}),
                jobs,
                releases,
                clocks: vec![1_200_000_000],
                owner_ids: (0..owner_count as u64).collect(),
                job_ids: ids,
            };
            let out = Simulation::with_releases(
                v.clocks.clone(),
                owner_count,
                v.jobs.clone(),
                v.releases.clone(),
            )
            .unwrap()
            .run()
            .unwrap();
            assert_eq!(
                out.duration_ps,
                expected["duration"].as_u64().unwrap(),
                "{case}"
            );
            for (j, row) in out.jobs.iter().zip(rows) {
                assert_eq!(
                    (j.ready_ps, j.start_ps, j.end_ps),
                    (
                        row[4].as_u64().unwrap(),
                        row[5].as_u64().unwrap(),
                        row[6].as_u64().unwrap()
                    ),
                    "{case}"
                );
            }
            let actual = construct(&v, &out).unwrap();
            let grants: Vec<_> = out
                .records
                .iter()
                .filter(|r| r.action == Action::Grant)
                .map(|r| v.job_ids[r.job_id as usize].clone())
                .collect();
            assert_eq!(json!(grants), expected["grants"], "{case}");
            let critical: Vec<_> = actual["observations"]["critical_path"]["records"]
                .as_array()
                .unwrap()
                .iter()
                .map(|x| json!([x["kind"], x["cause_job_id"], x["start_ps"], x["end_ps"]]))
                .collect();
            assert_eq!(json!(critical), expected["critical"], "{case}");
            for row in actual["busy_time_ps"].as_array().unwrap() {
                assert_eq!(
                    row["busy_time_ps"],
                    expected["busy"][row["owner_id"].to_string()],
                    "{case}"
                );
            }
            for interval in actual["observations"]["critical_path"]["records"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|x| x["kind"] == "service")
            {
                assert_eq!(
                    interval["predecessor_id"],
                    expected["chosen"][interval["cause_job_id"].as_str().unwrap()],
                    "{case}"
                );
            }
        }
    }
}
