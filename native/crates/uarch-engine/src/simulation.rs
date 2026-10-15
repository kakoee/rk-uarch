use crate::{Error, Kind, Wheel, next_edge};
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
}
#[derive(Debug, Serialize)]
pub struct JobObservation {
    pub job_id: u32,
    pub owner: u32,
    pub ready_ps: u64,
    pub start_ps: u64,
    pub end_ps: u64,
    pub blocking_predecessors: Vec<u32>,
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
/// Per-owner state is SoA. All mutations pass the event/grant target through check().
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
    fn check(&self, target: u32, owner: u32) -> Result<usize, Error> {
        debug_assert_eq!(target, owner, "foreign owner mutation");
        if target != owner {
            return Err(Error::ForeignOwner);
        }
        if owner as usize >= self.active.len() {
            return Err(Error::InvalidOwner);
        }
        Ok(owner as usize)
    }
    pub fn enqueue(&mut self, target: u32, owner: u32, job: usize) -> Result<(), Error> {
        let o = self.check(target, owner)?;
        self.waiting[o].push_back(job);
        Ok(())
    }
    fn grant(&mut self, target: u32, owner: u32) -> Result<Option<usize>, Error> {
        let o = self.check(target, owner)?;
        if self.active[o].is_some() {
            return Ok(None);
        }
        let job = self.waiting[o].pop_front();
        self.active[o] = job;
        Ok(job)
    }
    fn until(&mut self, target: u32, owner: u32, end_ps: u64) -> Result<(), Error> {
        let o = self.check(target, owner)?;
        self.busy_until_ps[o] = end_ps;
        Ok(())
    }
    fn complete(&mut self, target: u32, owner: u32, job: usize, t_ps: u64) -> Result<(), Error> {
        let o = self.check(target, owner)?;
        if self.active[o] != Some(job) || self.busy_until_ps[o] != t_ps {
            return Err(Error::InvalidEvent);
        }
        self.active[o] = None;
        self.previous[o] = Some(job);
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
                blocking_predecessors: Vec::new(),
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
    fn record(&mut self, i: usize, t_ps: u64, phase: u8, action: Action, event_seq: Option<u64>) {
        self.outcome.records.push(Record {
            ordinal: self.outcome.records.len() as u64,
            t_ps,
            phase,
            owner: self.jobs[i].owner,
            job_id: self.jobs[i].id,
            action,
            event_seq,
        });
    }
    fn enqueue_ready(&mut self, mut jobs: Vec<usize>, t_ps: u64, phase: u8) -> Result<(), Error> {
        jobs.sort_unstable();
        jobs.dedup();
        for i in jobs {
            if self.ready[i] || self.remaining[i] != 0 {
                return Err(Error::InvalidEvent);
            }
            self.ready[i] = true;
            self.observations[i].ready_ps = t_ps;
            let owner = self.jobs[i].owner;
            self.owners.enqueue(owner, owner, i)?;
            self.record(i, t_ps, phase, Action::Ready, None);
        }
        Ok(())
    }
    fn complete(
        &mut self,
        i: usize,
        target: u32,
        t_ps: u64,
        phase: u8,
    ) -> Result<Vec<usize>, Error> {
        if self.finished[i] {
            return Err(Error::InvalidEvent);
        }
        self.owners.complete(target, self.jobs[i].owner, i, t_ps)?;
        self.finished[i] = true;
        self.observations[i].end_ps = t_ps;
        self.outcome.completed_jobs += 1;
        self.outcome.duration_ps = t_ps;
        self.record(i, t_ps, phase, Action::Complete, None);
        let mut enabled = Vec::new();
        for &s in &self.successors[i] {
            self.remaining[s] -= 1;
            if self.remaining[s] == 0 {
                enabled.push(s);
            }
        }
        Ok(enabled)
    }
    pub fn run(mut self) -> Result<Outcome, Error> {
        while let Some(first) = self.wheel.peek() {
            let t_ps = first.t_ps;
            let mut enabled = Vec::new();
            // Drain all positive completions before initial readiness or grants.
            while self
                .wheel
                .peek()
                .is_some_and(|e| e.t_ps == t_ps && e.phase == 0)
            {
                let e = self.wheel.pop().expect("peeked event");
                let i = e.payload as usize;
                self.record(i, t_ps, 0, Action::Dispatch, Some(e.seq));
                match e.kind {
                    k if k == Kind::ComputeDone as u16 => {
                        enabled.extend(self.complete(i, e.target, t_ps, 0)?)
                    }
                    _ => return Err(Error::InvalidEvent),
                }
            }
            while self
                .wheel
                .peek()
                .is_some_and(|e| e.t_ps == t_ps && e.phase == 1)
            {
                let e = self.wheel.pop().expect("peeked event");
                let i = e.payload as usize;
                self.record(i, t_ps, 1, Action::Dispatch, Some(e.seq));
                match e.kind {
                    k if k == Kind::TaskReady as u16 => enabled.push(i),
                    _ => return Err(Error::InvalidEvent),
                }
            }
            self.enqueue_ready(enabled, t_ps, 1)?;
            // After each inline zero completion, enqueue its newly enabled jobs in ID
            // order, then restart owner order. Never enqueue retroactive phase0 events.
            loop {
                let candidate = (0..self.owners.active.len()).find(|&o| {
                    self.owners.active[o].is_none() && !self.owners.waiting[o].is_empty()
                });
                let Some(o) = candidate else {
                    break;
                };
                let owner = o as u32;
                let i = self.owners.grant(owner, owner)?.expect("eligible owner");
                let end_ps = match self.jobs[i].duration {
                    Delay::Picoseconds(ps) => t_ps.checked_add(ps).ok_or(Error::TimeOverflow)?,
                    Delay::Cycles { domain, n_cycles } => {
                        if n_cycles == 0 {
                            t_ps
                        } else {
                            next_edge(self.clocks[domain], t_ps, n_cycles)?
                        }
                    }
                };
                self.owners.until(owner, owner, end_ps)?;
                self.observations[i].start_ps = t_ps;
                let mut predecessors = self.jobs[i].dependencies.clone();
                if let Some(p) = self.owners.previous[o] {
                    predecessors.push(self.jobs[p].id);
                }
                predecessors.sort_unstable();
                predecessors.dedup();
                self.observations[i].blocking_predecessors = predecessors;
                self.record(i, t_ps, 2, Action::Grant, None);
                if end_ps == t_ps {
                    let ready = self.complete(i, owner, t_ps, 2)?;
                    self.enqueue_ready(ready, t_ps, 2)?;
                } else {
                    self.outcome.intervals.push(Interval {
                        owner,
                        job_id: self.jobs[i].id,
                        start_ps: t_ps,
                        end_ps,
                    });
                    self.wheel
                        .schedule(end_ps, 0, owner, Kind::ComputeDone, i as u32)?;
                }
            }
        }
        if self.outcome.completed_jobs != self.jobs.len() as u64 {
            return Err(Error::InvalidEvent);
        }
        self.outcome.jobs = self.observations;
        Ok(self.outcome)
    }
}
