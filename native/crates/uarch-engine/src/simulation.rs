use crate::{Error, Event, Kind, Wheel, next_edge};
use serde::Serialize;
use std::collections::VecDeque;

#[derive(Debug, Clone, Copy)]
pub enum Delay {
    Picoseconds(u64),
    Cycles { domain: usize, n_cycles: u64 },
}
#[derive(Debug, Clone)]
pub struct Job {
    pub id: u32,
    pub owner: u32,
    pub duration: Delay,
    pub dependencies: Vec<u32>,
}
#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
pub enum Action {
    Dispatch,
    Ready,
    Grant,
    Complete,
}
#[derive(Debug, Serialize)]
pub struct Record {
    pub ordinal: u64,
    pub t_ps: u64,
    pub phase: u8,
    pub owner: u32,
    pub job_id: u32,
    pub action: Action,
    pub event_seq: Option<u64>,
    pub event_target: u32,
    pub event_kind: u16,
    pub inline: bool,
}
#[derive(Debug, Serialize)]
pub struct JobObservation {
    pub job_id: u32,
    pub owner: u32,
    pub ready_ps: u64,
    pub start_ps: u64,
    pub end_ps: u64,
    /// Sorted unique declared dependencies plus the immediately prior completed
    /// job on this owner, even after an idle gap. NOT causal/critical-path evidence.
    pub dependency_resource_predecessors: Vec<u32>,
}
#[derive(Debug, Serialize)]
pub struct Interval {
    pub owner: u32,
    pub job_id: u32,
    pub start_ps: u64,
    pub end_ps: u64,
}
#[derive(Debug, Serialize)]
pub struct Outcome {
    pub duration_ps: u64,
    pub completed_jobs: u64,
    pub jobs: Vec<JobObservation>,
    pub intervals: Vec<Interval>,
    pub records: Vec<Record>,
}
impl Outcome {
    /// Private canonical observation bytes, not an EngineResult schema or public protocol.
    pub fn canonical_bytes(&self) -> Result<Vec<u8>, Error> {
        serde_json::to_vec(self).map_err(|_| Error::Serialization)
    }
}
/// Capability constructed only at the engine's dispatch boundary, from the actual
/// routed event and the resolved expected job owner. Never from an owner's self-assertion.
#[derive(Clone, Copy)]
struct Dispatch {
    event: Event,
    owner: u32,
    job: usize,
    inline: bool,
}
/// Per-owner state is SoA. Mutation methods require a checked dispatch capability.
#[derive(Debug)]
pub struct Owners {
    waiting: Vec<VecDeque<usize>>,
    active: Vec<Option<usize>>,
    busy_until_ps: Vec<u64>,
    previous: Vec<Option<usize>>,
}
impl Owners {
    pub fn new(count: usize) -> Self {
        Self {
            waiting: vec![VecDeque::new(); count],
            active: vec![None; count],
            busy_until_ps: vec![0; count],
            previous: vec![None; count],
        }
    }
    fn check(&self, ctx: &Dispatch) -> Result<usize, Error> {
        debug_assert_eq!(ctx.event.target, ctx.owner, "foreign owner mutation");
        debug_assert!(
            (ctx.event.target as usize) < self.active.len(),
            "missing owner target"
        );
        if ctx.event.target != ctx.owner {
            return Err(Error::ForeignOwner);
        }
        if ctx.event.target as usize >= self.active.len() {
            return Err(Error::InvalidOwner);
        }
        Ok(ctx.event.target as usize)
    }
    fn enqueue(&mut self, ctx: &Dispatch) -> Result<(), Error> {
        let o = self.check(ctx)?;
        self.waiting[o].push_back(ctx.job);
        Ok(())
    }
    fn grant(&mut self, ctx: &Dispatch) -> Result<(), Error> {
        let o = self.check(ctx)?;
        if self.active[o].is_some() || self.waiting[o].front() != Some(&ctx.job) {
            return Err(Error::InvalidEvent);
        }
        self.waiting[o].pop_front();
        self.active[o] = Some(ctx.job);
        Ok(())
    }
    fn until(&mut self, ctx: &Dispatch, end_ps: u64) -> Result<(), Error> {
        let o = self.check(ctx)?;
        self.busy_until_ps[o] = end_ps;
        Ok(())
    }
    fn complete(&mut self, ctx: &Dispatch) -> Result<(), Error> {
        let o = self.check(ctx)?;
        if self.active[o] != Some(ctx.job) || self.busy_until_ps[o] != ctx.event.t_ps {
            return Err(Error::InvalidEvent);
        }
        self.active[o] = None;
        self.previous[o] = Some(ctx.job);
        Ok(())
    }
    pub fn is_idle(&self, owner: u32) -> bool {
        self.active[owner as usize].is_none() && self.waiting[owner as usize].is_empty()
    }
}
#[derive(Debug)]
pub struct Simulation {
    clocks: Vec<u64>,
    jobs: Vec<Job>,
    owners: Owners,
    wheel: Wheel,
    remaining: Vec<usize>,
    successors: Vec<Vec<usize>>,
    ready: Vec<bool>,
    finished: Vec<bool>,
    observations: Vec<JobObservation>,
    outcome: Outcome,
}
impl Simulation {
    pub fn new(clocks: Vec<u64>, owner_count: usize, mut jobs: Vec<Job>) -> Result<Self, Error> {
        if clocks.is_empty() || clocks.contains(&0) {
            return Err(Error::InvalidClock);
        }
        if owner_count > u32::MAX as usize || jobs.len() > u32::MAX as usize {
            return Err(Error::InvalidOwner);
        }
        jobs.sort_by_key(|j| j.id);
        if jobs.windows(2).any(|p| p[0].id == p[1].id) {
            return Err(Error::DuplicateJob);
        }
        let mut successors = vec![Vec::new(); jobs.len()];
        let mut remaining = vec![0; jobs.len()];
        for (i, j) in jobs.iter().enumerate() {
            if j.owner as usize >= owner_count {
                return Err(Error::InvalidOwner);
            }
            if let Delay::Cycles { domain, .. } = j.duration
                && domain >= clocks.len()
            {
                return Err(Error::InvalidClock);
            }
            let mut deps = j.dependencies.clone();
            deps.sort_unstable();
            if deps.windows(2).any(|p| p[0] == p[1]) {
                return Err(Error::DuplicateDependency);
            }
            for dep in deps {
                let p = jobs
                    .binary_search_by_key(&dep, |j| j.id)
                    .map_err(|_| Error::MissingDependency)?;
                successors[p].push(i);
                remaining[i] += 1;
            }
        }
        let mut degree = remaining.clone();
        let mut queue: VecDeque<_> = degree
            .iter()
            .enumerate()
            .filter_map(|(i, &n)| if n == 0 { Some(i) } else { None })
            .collect();
        let mut visited = 0;
        while let Some(i) = queue.pop_front() {
            visited += 1;
            for &s in &successors[i] {
                degree[s] -= 1;
                if degree[s] == 0 {
                    queue.push_back(s);
                }
            }
        }
        if visited != jobs.len() {
            return Err(Error::DependencyCycle);
        }
        let mut wheel = Wheel::new(*clocks.iter().max().expect("nonempty clocks"))?;
        for (i, j) in jobs.iter().enumerate() {
            if remaining[i] == 0 {
                wheel.schedule(0, 1, j.owner, Kind::TaskReady, i as u32)?;
            }
        }
        let observations = jobs
            .iter()
            .map(|j| JobObservation {
                job_id: j.id,
                owner: j.owner,
                ready_ps: 0,
                start_ps: 0,
                end_ps: 0,
                dependency_resource_predecessors: Vec::new(),
            })
            .collect();
        Ok(Self {
            clocks,
            owners: Owners::new(owner_count),
            wheel,
            remaining,
            successors,
            ready: vec![false; jobs.len()],
            finished: vec![false; jobs.len()],
            jobs,
            observations,
            outcome: Outcome {
                duration_ps: 0,
                completed_jobs: 0,
                jobs: Vec::new(),
                intervals: Vec::new(),
                records: Vec::new(),
            },
        })
    }
    fn record(&mut self, ctx: &Dispatch, action: Action) {
        self.outcome.records.push(Record {
            ordinal: self.outcome.records.len() as u64,
            t_ps: ctx.event.t_ps,
            phase: ctx.event.phase,
            owner: ctx.owner,
            job_id: self.jobs[ctx.job].id,
            action,
            event_seq: Some(ctx.event.seq),
            event_target: ctx.event.target,
            event_kind: ctx.event.kind,
            inline: ctx.inline,
        });
    }
    fn ready(&mut self, ctx: &Dispatch) -> Result<(), Error> {
        let i = ctx.job;
        self.owners.check(ctx)?;
        if self.ready[i] || self.remaining[i] != 0 {
            return Err(Error::InvalidEvent);
        }
        self.owners.enqueue(ctx)?;
        self.ready[i] = true;
        self.observations[i].ready_ps = ctx.event.t_ps;
        self.record(ctx, Action::Ready);
        Ok(())
    }
    /// All resource/job state changes are handled on an actual addressed event.
    /// Completion emits recipient IDs; it does not decrement another owner's state.
    fn dispatch(&mut self, event: Event, inline: bool) -> Result<Vec<usize>, Error> {
        if (inline && event.phase != 2) || (!inline && event.phase > 1) {
            return Err(Error::InvalidEvent);
        }
        let i = event.payload as usize;
        let job = self.jobs.get(i).ok_or(Error::InvalidEvent)?;
        let ctx = Dispatch {
            event,
            owner: job.owner,
            job: i,
            inline,
        };
        self.owners.check(&ctx)?;
        self.record(&ctx, Action::Dispatch);
        match event.kind {
            k if k == Kind::TaskReady as u16
                && (event.phase == 1 || (inline && event.phase == 2)) =>
            {
                self.ready(&ctx)?;
            }
            k if k == Kind::DependencyReady as u16
                && (event.phase == 1 || (inline && event.phase == 2)) =>
            {
                self.owners.check(&ctx)?;
                if self.remaining[i] == 0 {
                    return Err(Error::InvalidEvent);
                }
                self.remaining[i] -= 1;
                if self.remaining[i] == 0 {
                    self.ready(&ctx)?;
                }
            }
            k if k == Kind::ComputeDone as u16
                && (event.phase == 0 || (inline && event.phase == 2)) =>
            {
                if self.finished[i] {
                    return Err(Error::InvalidEvent);
                }
                self.owners.complete(&ctx)?;
                self.finished[i] = true;
                self.observations[i].end_ps = event.t_ps;
                self.outcome.completed_jobs += 1;
                self.outcome.duration_ps = event.t_ps;
                self.record(&ctx, Action::Complete);
                return Ok(self.successors[i].clone());
            }
            k if k == Kind::OwnerGrant as u16 && inline && event.phase == 2 => {
                self.owners.grant(&ctx)?;
                let end_ps = match self.jobs[i].duration {
                    Delay::Picoseconds(ps) => {
                        event.t_ps.checked_add(ps).ok_or(Error::TimeOverflow)?
                    }
                    Delay::Cycles { domain, n_cycles } => {
                        if n_cycles == 0 {
                            event.t_ps
                        } else {
                            next_edge(self.clocks[domain], event.t_ps, n_cycles)?
                        }
                    }
                };
                self.owners.until(&ctx, end_ps)?;
                self.observations[i].start_ps = event.t_ps;
                let mut predecessors = self.jobs[i].dependencies.clone();
                if let Some(p) = self.owners.previous[event.target as usize] {
                    predecessors.push(self.jobs[p].id);
                }
                predecessors.sort_unstable();
                predecessors.dedup();
                self.observations[i].dependency_resource_predecessors = predecessors;
                self.record(&ctx, Action::Grant);
                if end_ps == event.t_ps {
                    let done =
                        self.wheel
                            .inline_event(event.target, Kind::ComputeDone, i as u32)?;
                    return self.dispatch(done, true);
                } else {
                    self.outcome.intervals.push(Interval {
                        owner: event.target,
                        job_id: self.jobs[i].id,
                        start_ps: event.t_ps,
                        end_ps,
                    });
                    self.wheel
                        .schedule(end_ps, 0, event.target, Kind::ComputeDone, i as u32)?;
                }
            }
            _ => return Err(Error::InvalidEvent),
        }
        Ok(Vec::new())
    }
    fn notify(&mut self, mut recipients: Vec<usize>, t_ps: u64, inline: bool) -> Result<(), Error> {
        // Keep multiplicity: a recipient may have several completed predecessors.
        // Sorting recipients preserves canonical job-ID FIFO order within each owner.
        recipients.sort_unstable();
        for i in recipients {
            let target = self.jobs[i].owner;
            if inline {
                let notification =
                    self.wheel
                        .inline_event(target, Kind::DependencyReady, i as u32)?;
                self.dispatch(notification, true)?;
            } else {
                self.wheel
                    .schedule(t_ps, 1, target, Kind::DependencyReady, i as u32)?;
            }
        }
        Ok(())
    }
    pub fn run(mut self) -> Result<Outcome, Error> {
        while let Some(first) = self.wheel.peek() {
            if first.phase > 1 {
                return Err(Error::InvalidEvent);
            }
            let t_ps = first.t_ps;
            let mut recipients = Vec::new();
            while self
                .wheel
                .peek()
                .is_some_and(|e| e.t_ps == t_ps && e.phase == 0)
            {
                let e = self.wheel.pop().expect("peeked event");
                recipients.extend(self.dispatch(e, false)?);
            }
            self.notify(recipients, t_ps, false)?;
            while self
                .wheel
                .peek()
                .is_some_and(|e| e.t_ps == t_ps && e.phase == 1)
            {
                let e = self.wheel.pop().expect("peeked event");
                if !self.dispatch(e, false)?.is_empty() {
                    return Err(Error::InvalidEvent);
                }
            }
            if self.wheel.peek().is_some_and(|e| e.t_ps == t_ps) {
                return Err(Error::InvalidEvent);
            }
            self.wheel.enter_inline_phase(t_ps)?;
            loop {
                let candidate = (0..self.owners.active.len()).find(|&o| {
                    self.owners.active[o].is_none() && !self.owners.waiting[o].is_empty()
                });
                let Some(o) = candidate else {
                    break;
                };
                let i = *self.owners.waiting[o].front().expect("eligible owner");
                let grant = self
                    .wheel
                    .inline_event(o as u32, Kind::OwnerGrant, i as u32)?;
                let recipients = self.dispatch(grant, true)?;
                self.notify(recipients, t_ps, true)?;
            }
        }
        if self.outcome.completed_jobs != self.jobs.len() as u64 {
            return Err(Error::InvalidEvent);
        }
        self.outcome.jobs = self.observations;
        Ok(self.outcome)
    }
}

#[cfg(test)]
pub(crate) mod stage2_routing_tests {
    use super::*;
    fn fixture(owner: u32) -> Simulation {
        Simulation::new(
            vec![1_000_000_000],
            2,
            vec![Job {
                id: 0,
                owner,
                duration: Delay::Picoseconds(0),
                dependencies: vec![],
            }],
        )
        .unwrap()
    }
    pub(crate) fn assert_wrong_ready(owner: u32, target: u32) {
        let mut s = fixture(owner);
        s.wheel = Wheel::new(1_000_000_000).unwrap();
        s.wheel.schedule(0, 1, target, Kind::TaskReady, 0).unwrap();
        let result = std::panic::catch_unwind(|| s.run());
        if cfg!(debug_assertions) {
            assert!(result.is_err());
        } else {
            assert!(matches!(
                result.unwrap(),
                Err(Error::ForeignOwner | Error::InvalidOwner)
            ));
        }
    }
    #[test]
    fn readiness_wrong_or_missing_target_refuses_in_engine() {
        for (owner, target) in [(1, 0), (0, 1), (0, 9)] {
            let mut s = fixture(owner);
            s.wheel = Wheel::new(1_000_000_000).unwrap();
            s.wheel.schedule(0, 1, target, Kind::TaskReady, 0).unwrap();
            let result = std::panic::catch_unwind(|| s.run());
            if cfg!(debug_assertions) {
                assert!(result.is_err(), "misrouted readiness returned success");
            } else {
                assert!(
                    matches!(
                        result.unwrap(),
                        Err(Error::ForeignOwner | Error::InvalidOwner)
                    ),
                    "misrouted readiness returned success"
                );
            }
        }
    }
    #[test]
    fn successor_grant_and_zero_handlers_refuse_foreign_targets() {
        for kind in [Kind::DependencyReady, Kind::OwnerGrant, Kind::ComputeDone] {
            for target in [0, 9] {
                let mut s = fixture(1);
                let e = Event::new(0, 0, target, kind, 2, 0);
                let result =
                    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| s.dispatch(e, true)));
                if cfg!(debug_assertions) {
                    assert!(result.is_err());
                } else {
                    assert!(matches!(
                        result.unwrap(),
                        Err(Error::ForeignOwner | Error::InvalidOwner)
                    ));
                }
            }
        }
    }
    #[test]
    fn inline_zero_closure_blocks_retroactive_phase_zero() {
        let mut s = fixture(0);
        let ready = s.wheel.pop().unwrap();
        s.dispatch(ready, false).unwrap();
        s.wheel.enter_inline_phase(0).unwrap();
        let grant = s.wheel.inline_event(0, Kind::OwnerGrant, 0).unwrap();
        s.dispatch(grant, true).unwrap();
        assert_eq!(s.outcome.completed_jobs, 1);
        assert_eq!(
            s.wheel.schedule(0, 0, 0, Kind::ComputeDone, 0),
            Err(Error::PastEvent)
        );
        // Advancing time resets the phase restriction; same-time phase3 is forward.
        assert!(s.wheel.schedule(0, 3, 0, Kind::StatSample, 0).is_ok());
        assert!(s.wheel.schedule(1, 0, 0, Kind::ComputeDone, 0).is_ok());
    }
    #[test]
    fn queued_unsupported_simulation_phase_returns_error() {
        let mut s = fixture(0);
        s.wheel = Wheel::new(1_000_000_000).unwrap();
        s.wheel.schedule(0, 2, 0, Kind::TaskReady, 0).unwrap();
        assert!(matches!(s.run(), Err(Error::InvalidEvent)));
    }
}
