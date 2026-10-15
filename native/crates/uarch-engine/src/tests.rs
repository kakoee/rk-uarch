//! Private K1 tests. Literal expectations are independent of the engine helpers.
use super::*;
use proptest::prelude::*;

fn job(id: u32, owner: u32, duration: Delay, deps: &[u32]) -> Job {
    Job {
        id,
        owner,
        duration,
        dependencies: deps.to_vec(),
    }
}
fn ps(value: u64) -> Delay {
    Delay::Picoseconds(value)
}
fn busy_zero() -> Vec<Job> {
    vec![
        job(0, 0, ps(3000), &[]),
        job(1, 1, ps(1000), &[]),
        job(2, 0, ps(0), &[1]),
        job(3, 1, ps(2000), &[2]),
    ]
}
fn run(jobs: Vec<Job>) -> Result<Outcome, Error> {
    Simulation::new(vec![1_200_000_000], 2, jobs)?.run()
}

#[test]
fn clock_literals_and_fractional_edges() {
    assert_eq!(next_edge(1_200_000_000, 0, 3), Ok(2500));
    assert_eq!(
        next_edge(1_200_000_000, 0, 1_000_000_000),
        Ok(833_333_333_334)
    );
    for (t, n, expected) in [
        (0, 0, 0),
        (1, 0, 834),
        (833, 0, 834),
        (834, 0, 834),
        (834, 1, 1667),
        (835, 0, 1667),
        (1667, 1, 2500),
    ] {
        assert_eq!(next_edge(1_200_000_000, t, n), Ok(expected));
    }
    assert_eq!(next_edge(2_000_000_000_000, 1, 1), Ok(1));
}
#[test]
fn clock_refuses_invalid_frequency_and_overflow() {
    assert_eq!(next_edge(0, 0, 0), Err(Error::InvalidClock));
    assert_eq!(next_edge(1, u64::MAX, 1), Err(Error::TimeOverflow));
    assert_eq!(next_edge(1, 0, u64::MAX), Err(Error::TimeOverflow));
}
#[test]
fn event_layout_and_tie_order() {
    assert_eq!(std::mem::size_of::<Event>(), 32);
    let mut w = Wheel::new(1_000_000_000).unwrap();
    for (phase, target) in [(2, 1), (0, 3), (0, 1), (0, 1), (1, 0)] {
        w.schedule(10, phase, target, Kind::TaskReady, 0).unwrap();
    }
    let got: Vec<_> = std::iter::from_fn(|| w.pop())
        .map(|e| (e.phase, e.target, e.seq))
        .collect();
    assert_eq!(
        got,
        vec![(0, 1, 2), (0, 1, 3), (0, 3, 1), (1, 0, 4), (2, 1, 0)]
    );
}
#[test]
fn arena_reuses_freed_slots_and_refuses_double_free() {
    let mut a = Arena::default();
    let e = Event::new(0, 0, 0, Kind::TaskReady, 0, 0);
    let first = a.insert(e);
    assert_eq!(a.remove(first), Some(e));
    assert_eq!(a.remove(first), None);
    assert_eq!(a.insert(e), first);
    assert_eq!(a.capacity_slots(), 1);
}
#[test]
fn wheel_levels_overflow_promotion_and_past_refusal() {
    let mut w = Wheel::new(1_000_000_000_000).unwrap();
    for t in [16_777_216, 4096, 4095, 0, 16_777_215] {
        w.schedule(t, 0, 0, Kind::TaskReady, 0).unwrap();
    }
    assert_eq!(w.level_counts(), (2, 2, 1));
    let times: Vec<_> = std::iter::from_fn(|| w.pop()).map(|e| e.t_ps).collect();
    assert_eq!(times, vec![0, 4095, 4096, 16_777_215, 16_777_216]);
    assert!(w.promotions() > 0);
    assert_eq!(
        w.schedule(0, 0, 0, Kind::TaskReady, 0),
        Err(Error::PastEvent)
    );
    assert_eq!(w.arena_slots(), 5);
    w.schedule(u64::MAX, 0, 0, Kind::End, 0).unwrap();
    assert_eq!(w.pop().unwrap().t_ps, u64::MAX);
}
#[test]
fn wheel_reuses_arena_after_warmup() {
    let mut w = Wheel::new(1).unwrap();
    for t in 0..100 {
        w.schedule(t, 0, 0, Kind::TaskReady, 0).unwrap();
        assert_eq!(w.pop().unwrap().t_ps, t);
    }
    assert_eq!(w.arena_slots(), 1);
}
#[test]
fn owner_foreign_mutation_is_refused() {
    let mut owners = Owners::new(2);
    let outcome =
        std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| owners.enqueue(0, 1, 0)));
    if cfg!(debug_assertions) {
        assert!(outcome.is_err());
    } else {
        assert_eq!(outcome.unwrap(), Err(Error::ForeignOwner));
    }
    assert!(owners.is_idle(1));
}
#[test]
fn busy_owner_zero_grant_is_5000_not_3000() {
    let r = run(busy_zero()).unwrap();
    assert_eq!(r.duration_ps, 5000);
    assert_eq!(
        (r.jobs[2].ready_ps, r.jobs[2].start_ps, r.jobs[2].end_ps),
        (1000, 3000, 3000)
    );
    assert_eq!(r.jobs.len(), 4);
    assert_eq!(r.completed_jobs, 4);
    assert_eq!(r.intervals.len(), 3); // zero grant owns, but has no positive interval
    assert!(
        r.records
            .iter()
            .any(|e| e.job_id == 2 && e.action == Action::Complete && e.phase == 2)
    );
}
#[test]
fn critical_path_overlap_and_fifo_serialization() {
    let r = run(vec![
        job(0, 0, ps(3000), &[]),
        job(1, 1, ps(1000), &[]),
        job(2, 1, ps(4000), &[0, 1]),
        job(3, 0, ps(2000), &[0]),
    ])
    .unwrap();
    assert_eq!(r.duration_ps, 7000); // max(3000,1000)+4000
    assert_eq!(
        r.jobs.iter().map(|j| j.end_ps).collect::<Vec<_>>(),
        vec![3000, 1000, 7000, 5000]
    );
    let r = run(vec![job(4, 0, ps(7), &[]), job(2, 0, ps(3), &[])]).unwrap();
    assert_eq!(
        r.jobs
            .iter()
            .map(|j| (j.job_id, j.start_ps, j.end_ps))
            .collect::<Vec<_>>(),
        vec![(2, 0, 3), (4, 3, 10)]
    );
}
#[test]
fn zero_closure_is_canonical_and_completes_once() {
    let r = run(vec![
        job(0, 1, ps(0), &[]),
        job(1, 0, ps(0), &[0]),
        job(2, 1, ps(3000), &[1]),
    ])
    .unwrap();
    assert_eq!(r.duration_ps, 3000);
    assert_eq!(r.completed_jobs, 3);
    assert_eq!(
        r.records
            .iter()
            .filter(|r| r.action == Action::Complete)
            .count(),
        3
    );
    assert!(r.records.windows(2).all(|p| p[0].ordinal < p[1].ordinal));
}
#[test]
fn cycle_delay_uses_resolved_domain_without_drift() {
    let r = run(vec![job(
        0,
        0,
        Delay::Cycles {
            domain: 0,
            n_cycles: 1_000_000_000,
        },
        &[],
    )])
    .unwrap();
    assert_eq!(r.duration_ps, 833_333_333_334);
    let r = run(vec![
        job(0, 0, ps(835), &[]),
        job(
            1,
            0,
            Delay::Cycles {
                domain: 0,
                n_cycles: 1,
            },
            &[0],
        ),
    ])
    .unwrap();
    assert_eq!(r.duration_ps, 2500);
}
#[test]
fn graph_refuses_duplicates_missing_edges_cycles_owners_domains() {
    for (jobs, error) in [
        (
            vec![job(0, 0, ps(0), &[]), job(0, 0, ps(0), &[])],
            Error::DuplicateJob,
        ),
        (vec![job(0, 0, ps(0), &[1])], Error::MissingDependency),
        (vec![job(0, 0, ps(0), &[0])], Error::DependencyCycle),
        (
            vec![job(0, 0, ps(0), &[1]), job(1, 1, ps(0), &[0])],
            Error::DependencyCycle,
        ),
        (
            vec![job(0, 0, ps(0), &[]), job(1, 1, ps(0), &[0, 0])],
            Error::DuplicateDependency,
        ),
        (vec![job(0, 2, ps(0), &[])], Error::InvalidOwner),
        (
            vec![job(
                0,
                0,
                Delay::Cycles {
                    domain: 1,
                    n_cycles: 1,
                },
                &[],
            )],
            Error::InvalidClock,
        ),
    ] {
        assert_eq!(run(jobs).unwrap_err(), error);
    }
    assert_eq!(
        Simulation::new(vec![0], 1, vec![]).unwrap_err(),
        Error::InvalidClock
    );
    assert_eq!(
        run(vec![job(0, 0, ps(u64::MAX), &[]), job(1, 0, ps(1), &[0])]).unwrap_err(),
        Error::TimeOverflow
    );
}
#[test]
fn canonical_replay_private_bytes() {
    let expected = run(busy_zero()).unwrap().canonical_bytes().unwrap();
    for _ in 0..3 {
        assert_eq!(
            run(busy_zero()).unwrap().canonical_bytes().unwrap(),
            expected
        );
    }
    let mut shuffled = busy_zero();
    shuffled.reverse();
    assert_eq!(run(shuffled).unwrap().canonical_bytes().unwrap(), expected);
    println!(
        "UARCH_K1_REPLAY_V1={}",
        std::str::from_utf8(&expected).unwrap()
    );
    // Test-only evidence sink: never a public engine JSON/subprocess interface.
    if let Some(path) = std::env::var_os("UARCH_K1_REPLAY_OUT") {
        std::fs::write(path, expected).unwrap();
    }
}
#[test]
fn csr_mesh_torus_routes_and_multiple_nocs() {
    let mesh = Topology::new(3, 2, false, Direction::Positive).unwrap();
    assert_eq!(mesh.route(0, 5).unwrap(), vec![0, 1, 2, 5]);
    assert_eq!(mesh.route(4, 4).unwrap(), vec![4]);
    let torus = Topology::new(4, 2, true, Direction::Positive).unwrap();
    let reverse = Topology::new(4, 2, true, Direction::Negative).unwrap();
    assert_eq!(torus.route(0, 3).unwrap(), vec![0, 3]);
    assert_eq!(torus.route(0, 2).unwrap(), vec![0, 1, 2]);
    assert_eq!(reverse.route(0, 2).unwrap(), vec![0, 3, 2]);
    for topology in [mesh, torus, reverse] {
        for from in 0..topology.nodes() {
            for to in 0..topology.nodes() {
                let route = topology.route(from, to).unwrap();
                assert!(
                    route
                        .windows(2)
                        .all(|p| topology.neighbors(p[0]).contains(&p[1]))
                );
            }
        }
        assert_eq!(
            topology.route(topology.nodes(), 0),
            Err(Error::InvalidRoute)
        );
    }
    assert_eq!(
        Topology::new(0, 1, false, Direction::Positive).unwrap_err(),
        Error::InvalidRoute
    );
}
proptest! {
    #[test]
    fn rounded_edges_never_early(freq_hz in 1u64..=1_000_000_000_000, k in 0u64..1_000_000) {
        let t=next_edge(freq_hz,0,k).unwrap();
        let error=u128::from(t)*u128::from(freq_hz)-u128::from(k)*1_000_000_000_000u128;
        prop_assert!(error<u128::from(freq_hz));
        prop_assert_eq!(next_edge(freq_hz,t,0).unwrap(),t);
    }
    #[test]
    fn wheel_matches_sorted_reference(input in prop::collection::vec((0u64..50_000_000,0u8..4,0u32..8),0..80)) {
        let mut w=Wheel::new(1_000_000_000_000).unwrap();
        let mut reference=Vec::new();
        for (seq,(t,phase,target)) in input.into_iter().enumerate() {
            w.schedule(t,phase,target,Kind::TaskReady,0).unwrap(); reference.push((t,phase,target,seq as u64));
        }
        reference.sort();
        let got:Vec<_>=std::iter::from_fn(||w.pop()).map(|e|(e.t_ps,e.phase,e.target,e.seq)).collect();
        prop_assert_eq!(got,reference);
    }
}

#[test]
fn resolved_domains_and_zero_cycles_at_fractional_start() {
    let jobs = vec![
        job(0, 0, ps(835), &[]),
        job(
            1,
            0,
            Delay::Cycles {
                domain: 0,
                n_cycles: 0,
            },
            &[0],
        ),
        job(
            2,
            1,
            Delay::Cycles {
                domain: 1,
                n_cycles: 3,
            },
            &[1],
        ),
    ];
    let r = Simulation::new(vec![1_200_000_000, 1_000_000_000], 2, jobs)
        .unwrap()
        .run()
        .unwrap();
    assert_eq!((r.jobs[1].start_ps, r.jobs[1].end_ps), (835, 835));
    assert_eq!(r.duration_ps, 4000); // 1GHz first edge 1000 + 3 cycles
}
#[test]
fn readiness_is_fifo_and_simultaneous_completions_join_by_id() {
    let r = run(vec![
        job(0, 0, ps(3000), &[]),
        job(1, 1, ps(1000), &[]),
        job(2, 0, ps(1000), &[1]),
        job(3, 0, ps(1000), &[0]),
        job(4, 1, ps(2000), &[1]),
    ])
    .unwrap();
    assert_eq!((r.jobs[2].start_ps, r.jobs[3].start_ps), (3000, 4000));
    assert_eq!(r.duration_ps, 5000);
    for owner in 0..2 {
        let intervals: Vec<_> = r.intervals.iter().filter(|v| v.owner == owner).collect();
        assert!(intervals.windows(2).all(|p| p[0].end_ps <= p[1].start_ps));
    }
    let r = run(vec![
        job(0, 0, ps(1000), &[]),
        job(1, 1, ps(1000), &[]),
        job(2, 0, ps(1), &[1]),
        job(3, 0, ps(1), &[0]),
    ])
    .unwrap();
    assert_eq!((r.jobs[2].start_ps, r.jobs[3].start_ps), (1000, 1001));
}
proptest! {
    #[test]
    fn wheel_interleaved_scheduling_matches_reference(steps in prop::collection::vec((0u64..50_000_000,0u8..4,0u32..8,any::<bool>()),1..120)) {
        let mut w=Wheel::new(1_000_000_000_000).unwrap();
        let mut reference=Vec::new();let mut now=0;
        for (seq,(offset,phase,target,pop)) in steps.into_iter().enumerate() {
            let t=now+offset;w.schedule(t,phase,target,Kind::TaskReady,0).unwrap();
            reference.push((t,phase,target,seq as u64));reference.sort();
            if pop {let expected=reference.remove(0);let e=w.pop().unwrap();
                prop_assert_eq!((e.t_ps,e.phase,e.target,e.seq),expected);now=e.t_ps;}
        }
        let got:Vec<_>=std::iter::from_fn(||w.pop()).map(|e|(e.t_ps,e.phase,e.target,e.seq)).collect();
        prop_assert_eq!(got,reference);
    }
}
