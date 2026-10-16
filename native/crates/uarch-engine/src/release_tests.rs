//! Private mechanics tests, never successful public MappedEngineJob execution.
use crate::{Action, Delay, Job, Simulation, next_edge};
fn job(id: u32, owner: u32, duration: Delay, deps: &[u32]) -> Job {
    Job {
        id,
        owner,
        duration,
        dependencies: deps.to_vec(),
    }
}
fn ps(n: u64) -> Delay {
    Delay::Picoseconds(n)
}
#[test]
fn raw_edge_and_owned_zero_have_distinct_laws() {
    assert_eq!(next_edge(1_200_000_000, 835, 0), Ok(1667));
    let o = Simulation::with_releases(
        vec![1_200_000_000],
        1,
        vec![job(
            0,
            0,
            Delay::Cycles {
                domain: 0,
                n_cycles: 0,
            },
            &[],
        )],
        vec![(0, 835)],
    )
    .unwrap()
    .run()
    .unwrap();
    assert_eq!(
        (o.jobs[0].ready_ps, o.jobs[0].start_ps, o.jobs[0].end_ps),
        (835, 835, 835)
    );
    assert!(o.intervals.is_empty());
}
#[test]
fn release_waits_for_dependencies_and_owner() {
    let o = Simulation::with_releases(
        vec![1_000_000_000],
        2,
        vec![
            job(0, 0, ps(20), &[]),
            job(1, 0, ps(3), &[]),
            job(2, 1, ps(1), &[0]),
            job(3, 1, ps(0), &[2]),
        ],
        vec![(1, 5), (2, 10), (3, 30)],
    )
    .unwrap()
    .run()
    .unwrap();
    let times: Vec<_> = o
        .jobs
        .iter()
        .map(|j| (j.ready_ps, j.start_ps, j.end_ps))
        .collect();
    assert_eq!(
        times,
        vec![(0, 0, 20), (5, 20, 23), (20, 20, 21), (30, 30, 30)]
    );
}
#[test]
fn cycles_start_at_actual_grant_after_release() {
    let o = Simulation::with_releases(
        vec![1_200_000_000],
        1,
        vec![
            job(0, 0, ps(835), &[]),
            job(
                1,
                0,
                Delay::Cycles {
                    domain: 0,
                    n_cycles: 1,
                },
                &[],
            ),
        ],
        vec![(1, 3)],
    )
    .unwrap()
    .run()
    .unwrap();
    assert_eq!(
        (o.jobs[1].ready_ps, o.jobs[1].start_ps, o.jobs[1].end_ps),
        (3, 835, 2500)
    );
}
#[test]
fn completion_release_and_dependency_readiness_batch_before_inline_zero() {
    // Release event for job2 was scheduled before the completion's notification
    // for job1. FIFO must batch newly ready phase1 jobs by ID, not event seq.
    let o = Simulation::with_releases(
        vec![1_000_000_000],
        2,
        vec![
            job(0, 1, ps(10), &[]),
            job(1, 0, ps(0), &[0]),
            job(2, 0, ps(0), &[]),
            job(3, 0, ps(0), &[1]),
        ],
        vec![(2, 10)],
    )
    .unwrap()
    .run()
    .unwrap();
    let grants: Vec<_> = o
        .records
        .iter()
        .filter(|r| r.action == Action::Grant)
        .map(|r| r.job_id)
        .collect();
    assert_eq!(grants, vec![0, 1, 2, 3]);
    assert!(
        o.records
            .iter()
            .filter(|r| r.t_ps == 10 && r.phase == 1)
            .all(|r| r.ordinal
                < o.records
                    .iter()
                    .find(|r| r.t_ps == 10 && r.action == Action::Grant)
                    .unwrap()
                    .ordinal)
    );
}
#[test]
fn owned_zero_at_u64_max_survives_raw_alignment_overflow() {
    assert_eq!(
        next_edge(1_000_000_000, u64::MAX, 0),
        Err(crate::Error::TimeOverflow)
    );
    let o = Simulation::with_releases(
        vec![1_000_000_000],
        1,
        vec![job(
            0,
            0,
            Delay::Cycles {
                domain: 0,
                n_cycles: 0,
            },
            &[],
        )],
        vec![(0, u64::MAX)],
    )
    .unwrap()
    .run()
    .unwrap();
    assert_eq!(o.duration_ps, u64::MAX);
}
