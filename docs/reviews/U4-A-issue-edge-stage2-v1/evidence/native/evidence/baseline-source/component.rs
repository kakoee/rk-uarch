//! Component phase executor. Every published activity is created by a dispatched transition.
//! No Python durations, expected rows, hardware work inferred from the input, or public trust.
use crate::{
    Event, Kind, Wheel,
    admission::Trust,
    carrier::{Result, refuse},
    component_admission::{self, Admitted, TaskKind},
    next_edge,
};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
fn overflow() -> crate::Refusal {
    refuse("TimeOverflow", "", "checked component arithmetic")
}
pub(crate) fn add(a: u64, b: u64) -> Result<u64> {
    a.checked_add(b).ok_or_else(overflow)
}
pub(crate) fn mul(a: u64, b: u64) -> Result<u64> {
    a.checked_mul(b).ok_or_else(overflow)
}
fn edge(hz: u64, t: u64, n: u64) -> Result<u64> {
    next_edge(hz, t, n).map_err(|_| overflow())
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct Ratio {
    pub n: u128,
    pub d: u128,
}
impl Ratio {
    pub(crate) fn new(n: u128, d: u128) -> Result<Self> {
        if d == 0 {
            return Err(overflow());
        }
        let (mut a, mut b) = (n, d);
        while b != 0 {
            (a, b) = (b, a % b)
        }
        Ok(Self { n: n / a, d: d / a })
    }
    pub(crate) fn integer(n: u64) -> Self {
        Self { n: n.into(), d: 1 }
    }
    pub(crate) fn ceil(self) -> Result<u64> {
        u64::try_from(self.n.div_ceil(self.d)).map_err(|_| overflow())
    }
    pub(crate) fn plus(self, z: Self) -> Result<Self> {
        let mut a = self.d;
        let mut b = z.d;
        while b != 0 {
            (a, b) = (b, a % b)
        }
        let x = z.d / a;
        let y = self.d / a;
        Self::new(
            self.n
                .checked_mul(x)
                .and_then(|n| z.n.checked_mul(y).and_then(|m| n.checked_add(m)))
                .ok_or_else(overflow)?,
            self.d.checked_mul(x).ok_or_else(overflow)?,
        )
    }
    pub(crate) fn max_integer(self, n: u64) -> Result<Self> {
        if self.n >= u128::from(n).checked_mul(self.d).ok_or_else(overflow)? {
            Ok(self)
        } else {
            Ok(Self::integer(n))
        }
    }
}
#[derive(Clone, Debug)]
pub(crate) struct Phase {
    pub name: &'static str,
    pub owner: u64,
    pub category: &'static str,
    pub domain: Option<usize>,
    pub cycles: u64,
    pub occupies: bool,
    pub contended: bool,
}
#[derive(Clone, Debug)]
pub(crate) struct Activity {
    pub job: usize,
    pub sequence: usize,
    pub phase: Phase,
    pub alignment: bool,
    pub ready: u64,
    pub start: u64,
    pub end: u64,
    pub dispatch: u64,
    pub completion: u64,
    pub causes: Vec<(usize, &'static str)>,
    pub ratio: Option<(Ratio, Ratio)>,
    pub clock_aligned: Option<u64>,
}
#[derive(Clone, Debug)]
pub(crate) struct Dispatch {
    pub activity: usize,
    pub completion: bool,
    pub time: u64,
    pub phase: u8,
    pub seq: u64,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ObservationVersion {
    V2,
    V3,
}
#[derive(Clone, Debug)]
pub(crate) struct Sequence {
    pub job: usize,
    pub request: Option<String>,
    pub engine: Option<u64>,
    pub source: Option<String>,
    pub destination: Option<String>,
    pub payload: u64,
    pub write: bool,
    pub route: Option<usize>,
    pub phases: Vec<Phase>,
    pub step: usize,
    pub ready: u64,
    pub reservation: Option<u64>,
    pub issue: Option<u64>,
    pub end: Option<u64>,
    pub activities: Vec<usize>,
    active: bool,
    service_ready: bool,
    enabled: bool,
    credit_causes: Vec<usize>,
}
#[derive(Clone, Debug, Default)]
pub(crate) struct JobState {
    pub ready: Option<u64>,
    pub start: Option<u64>,
    pub end: Option<u64>,
    pub useful: u64,
    pub issued: u64,
    pub sequences: Vec<usize>,
}
#[derive(Clone, Debug, Default)]
pub(crate) struct Counts {
    pub mac: u64,
    pub issued: u64,
    pub sram_read: u64,
    pub sram_write: u64,
    pub read: u64,
    pub write: u64,
    pub read_txn: u64,
    pub write_txn: u64,
    pub unicast: u64,
}
impl Counts {
    pub(crate) fn merge(&mut self, c: &Self) -> Result<()> {
        self.mac = add(self.mac, c.mac)?;
        self.issued = add(self.issued, c.issued)?;
        self.sram_read = add(self.sram_read, c.sram_read)?;
        self.sram_write = add(self.sram_write, c.sram_write)?;
        self.read = add(self.read, c.read)?;
        self.write = add(self.write, c.write)?;
        self.read_txn = add(self.read_txn, c.read_txn)?;
        self.write_txn = add(self.write_txn, c.write_txn)?;
        self.unicast = add(self.unicast, c.unicast)?;
        Ok(())
    }
}
#[derive(Clone, Debug, Default)]
pub(crate) struct Allocation {
    pub start: Option<u64>,
    pub end: Option<u64>,
}
#[derive(Clone, Debug)]
pub(crate) struct ReservationOpportunity {
    pub time: u64,
    pub event_cursor: u64,
    pub granted: Vec<usize>,
}
pub(crate) struct Runtime {
    pub observations: ObservationVersion,
    pub reservation_opportunities: Vec<ReservationOpportunity>,
    eligibility_dirty: bool,
    pending_issue: BTreeMap<u64, BTreeSet<usize>>,
    pub allocations: Vec<Allocation>,
    pub activities: Vec<Activity>,
    pub events: Vec<Dispatch>,
    pub sequences: Vec<Sequence>,
    pub jobs: Vec<JobState>,
    pub counts: Counts,
    pub per_job: Vec<Counts>,
    pub duration: u64,
    pub max_live_events: usize,
    wheel: Wheel,
    pending_count: usize,
    busy: BTreeMap<u64, usize>,
    last: BTreeMap<u64, usize>,
    channels: BTreeMap<u64, Ratio>,
    inflight: BTreeMap<u64, BTreeSet<usize>>,
    now: u64,
}
fn endpoint(a: &Activity, completion: bool) -> Kind {
    let (start, end) = if a.alignment {
        (Kind::TaskReady, Kind::DependencyReady)
    } else {
        match a.phase.name {
            "compute_overhead" | "compute_stage" | "compute_wave" | "compute_drain" => {
                (Kind::OwnerGrant, Kind::ComputeDone)
            }
            "read_port" => (Kind::OwnerGrant, Kind::DmaDone),
            "write_port" => (Kind::OwnerGrant, Kind::MemResp),
            "channel_service" | "dram_latency" => (Kind::MemReq, Kind::MemResp),
            "request_noc" | "response_noc" | "unicast_noc" => (Kind::NocHead, Kind::NocTail),
            "ack" => (Kind::TaskReady, Kind::DmaDone),
            "dma_issue" => (Kind::TaskReady, Kind::DmaIssue),
            "barrier" => (Kind::SyncArrive, Kind::BarrierRelease),
            _ => unreachable!("typed phase"),
        }
    };
    if completion { end } else { start }
}
impl Runtime {
    fn new(v: &Admitted) -> Result<Self> {
        Self::new_version(v, ObservationVersion::V2)
    }
    fn new_version(v: &Admitted, observations: ObservationVersion) -> Result<Self> {
        let mut r = Self {
            observations,
            reservation_opportunities: vec![],
            eligibility_dirty: true,
            pending_issue: BTreeMap::new(),
            allocations: v
                .graph
                .buffers
                .iter()
                .map(|b| Allocation {
                    start: if b.persistent { Some(0) } else { None },
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
            wheel: Wheel::new(*v.hardware.freq.iter().max().unwrap()).map_err(|_| overflow())?,
            pending_count: 0,
            busy: BTreeMap::new(),
            last: BTreeMap::new(),
            channels: BTreeMap::new(),
            inflight: BTreeMap::new(),
            now: 0,
        };
        let h = &v.hardware;
        let phase = |name, owner, category, domain, cycles, occupies, contended| Phase {
            name,
            owner,
            category,
            domain,
            cycles,
            occupies,
            contended,
        };
        for (job, t) in v.graph.jobs.iter().enumerate() {
            let mut seq = Sequence {
                job,
                request: None,
                engine: None,
                source: None,
                destination: None,
                payload: 0,
                write: false,
                route: None,
                phases: vec![],
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
            match &t.kind {
                TaskKind::Compute { core, m, k, n } => {
                    if v.owners[&format!("matrix:{core}")] != t.owner {
                        return Err(refuse("InvalidResource", "", "typed matrix owner"));
                    }
                    let input = mul(2, add(mul(*m, *k)?, mul(*k, *n)?)?)?;
                    let output = mul(2, mul(*m, *n)?)?;
                    seq.phases = vec![
                        phase(
                            "compute_overhead",
                            t.owner,
                            "overhead",
                            Some(0),
                            h.overhead,
                            true,
                            true,
                        ),
                        phase(
                            "compute_stage",
                            t.owner,
                            "compute",
                            Some(0),
                            input.div_ceil(h.operand_rate),
                            true,
                            false,
                        ),
                        phase(
                            "compute_wave",
                            t.owner,
                            "compute",
                            Some(0),
                            add(h.wave_fill_drain, *m)?,
                            true,
                            false,
                        ),
                        phase(
                            "compute_drain",
                            t.owner,
                            "compute",
                            Some(0),
                            output.div_ceil(h.operand_rate),
                            true,
                            false,
                        ),
                    ];
                }
                TaskKind::Barrier => {
                    seq.phases = vec![phase(
                        "barrier",
                        t.owner,
                        "sync",
                        Some(1),
                        h.barrier_cycles,
                        false,
                        false,
                    )];
                }
                TaskKind::Unicast {
                    source,
                    destination,
                    payload,
                    route,
                } => {
                    let route_data = &v.graph.routes[*route];
                    seq.request = Some(t.id.clone());
                    seq.source = Some(source.clone());
                    seq.destination = Some(destination.clone());
                    seq.payload = *payload;
                    seq.route = Some(*route);
                    seq.phases = vec![phase(
                        "unicast_noc",
                        route_data.owner,
                        "noc",
                        Some(1),
                        mul(route_data.hops, h.hop_cycles)?,
                        route_data.hops > 0,
                        false,
                    )];
                }
                TaskKind::Dma {
                    engine,
                    core,
                    write,
                    source,
                    destination,
                    fragments,
                } => {
                    for f in fragments {
                        let mut s = seq.clone();
                        s.request = Some(f.id.clone());
                        s.engine = Some(*engine);
                        s.source = Some(source.clone());
                        s.destination = Some(destination.clone());
                        s.payload = f.payload;
                        s.write = *write;
                        s.route = Some(f.route);
                        let route = &v.graph.routes[f.route];
                        let port = v.owners[&format!("dma_port:{core}")];
                        let channel = v.owners[&format!("channel:{}", f.channel)];
                        let hops = mul(route.hops, h.hop_cycles)?;
                        let mut phases = vec![];
                        if observations == ObservationVersion::V3 {
                            phases.push(phase(
                                "dma_issue",
                                t.owner,
                                "memory",
                                Some(0),
                                0,
                                false,
                                false,
                            ));
                        }
                        if *write {
                            phases.push(phase(
                                "write_port",
                                port,
                                "memory",
                                Some(0),
                                f.payload.div_ceil(h.port_rate),
                                true,
                                true,
                            ));
                        }
                        phases.extend([
                            phase(
                                "request_noc",
                                route.owner,
                                "noc",
                                Some(1),
                                hops,
                                route.hops > 0,
                                false,
                            ),
                            phase(
                                "dram_latency",
                                channel,
                                "memory",
                                Some(2),
                                h.dram_latency,
                                false,
                                false,
                            ),
                            phase("channel_service", channel, "memory", None, 0, true, true),
                            phase(
                                "response_noc",
                                route.owner,
                                "noc",
                                Some(1),
                                hops,
                                route.hops > 0,
                                false,
                            ),
                        ]);
                        phases.push(if *write {
                            phase("ack", port, "memory", Some(0), 0, false, false)
                        } else {
                            phase(
                                "read_port",
                                port,
                                "memory",
                                Some(0),
                                f.payload.div_ceil(h.port_rate),
                                true,
                                true,
                            )
                        });
                        s.phases = phases;
                        r.jobs[job].sequences.push(r.sequences.len());
                        r.sequences.push(s);
                    }
                    continue;
                }
            }
            r.jobs[job].sequences.push(r.sequences.len());
            r.sequences.push(seq);
        }
        let events_per_sequence = match observations {
            ObservationVersion::V2 => 24,
            ObservationVersion::V3 => 28,
        };
        if r.sequences.len() > crate::protocol::MAX_EVENTS / events_per_sequence {
            return Err(refuse(
                "CapacityExceeded",
                "",
                "component phase inventory bound",
            ));
        }
        Ok(r)
    }
    fn event(&mut self, activity: usize, completion: bool, queued: Option<Event>) -> Result<u64> {
        let a = &self.activities[activity];
        let target = u32::try_from(a.phase.owner).map_err(|_| overflow())?;
        let kind = endpoint(a, completion);
        let event = if let Some(e) = queued {
            if e.target != target
                || e.payload as usize != activity
                || e.kind != kind as u16
                || e.t_ps != self.now
            {
                return Err(refuse("InternalError", "", "foreign component dispatch"));
            }
            e
        } else {
            self.wheel
                .inline_event(
                    target,
                    kind,
                    u32::try_from(activity).map_err(|_| overflow())?,
                )
                .map_err(|_| refuse("InternalError", "", "component inline ordering"))?
        };
        let ordinal = self.events.len() as u64;
        self.events.push(Dispatch {
            activity,
            completion,
            time: event.t_ps,
            phase: event.phase,
            seq: event.seq,
        });
        Ok(ordinal)
    }
    fn causes(&self, s: usize, start: u64, resource: Option<usize>) -> Vec<(usize, &'static str)> {
        let sequence = &self.sequences[s];
        let mut causes = vec![];
        if let Some(&previous) = sequence.activities.last()
            && self.activities[previous].end == start
        {
            causes.push((previous, "sequence"));
        }
        if let Some(previous) = resource
            && self.activities[previous].end == start
        {
            causes.push((previous, "resource"));
        }
        if sequence.activities.is_empty() {
            for &previous in &sequence.credit_causes {
                if self.activities[previous].end == start {
                    causes.push((previous, "credit"));
                }
            }
        }
        causes
    }
    fn dependency_causes(
        &self,
        v: &Admitted,
        s: usize,
        start: u64,
        causes: &mut Vec<(usize, &'static str)>,
    ) {
        if !self.sequences[s].activities.is_empty() {
            return;
        }
        for &(before, after) in &v.graph.dependencies {
            if after == self.sequences[s].job && self.jobs[before].end == Some(start) {
                for &seq in &self.jobs[before].sequences {
                    if let Some(&a) = self.sequences[seq].activities.last()
                        && self.activities[a].end == start
                    {
                        causes.push((a, "dependency"));
                    }
                }
            }
        }
    }
    fn activity(
        &mut self,
        v: &Admitted,
        s: usize,
        phase: Phase,
        alignment: bool,
        span: (u64, u64, Option<usize>, Option<(Ratio, Ratio)>),
    ) -> Result<usize> {
        let (ready, end, resource, ratio) = span;
        let index = self.activities.len();
        let mut causes = self.causes(s, self.now, resource);
        self.dependency_causes(v, s, self.now, &mut causes);
        causes.sort_unstable();
        causes.dedup();
        let job = self.sequences[s].job;
        let clock_aligned =
            if phase.domain.is_some() && !(phase.name.ends_with("_noc") && !phase.occupies) {
                Some(if alignment { end } else { self.now })
            } else {
                None
            };
        self.activities.push(Activity {
            clock_aligned,
            job,
            sequence: s,
            phase,
            alignment,
            ready,
            start: self.now,
            end,
            dispatch: 0,
            completion: 0,
            causes,
            ratio,
        });
        let ordinal = self.event(index, false, None)?;
        self.activities[index].dispatch = ordinal;
        self.sequences[s].activities.push(index);
        if self.jobs[job].start.is_none() {
            self.jobs[job].start = Some(self.now);
            for (i, b) in v.graph.buffers.iter().enumerate() {
                if !b.persistent && b.producer == Some(job) {
                    self.allocations[i].start = Some(self.now);
                }
            }
        }
        Ok(index)
    }
    fn start(&mut self, v: &Admitted, s: usize) -> Result<()> {
        let p = self.sequences[s].phases[self.sequences[s].step].clone();
        let ready = self.sequences[s].ready;
        let previous = if p.contended {
            self.last.get(&p.owner).copied()
        } else {
            None
        };
        if p.contended {
            self.busy.insert(p.owner, s);
        }
        let clocked = p.domain.is_some() && !(p.name.ends_with("_noc") && !p.occupies);
        self.sequences[s].active = true;
        if clocked {
            let end = edge(v.hardware.freq[p.domain.unwrap()], self.now, 0)?;
            let a = self.activity(v, s, p, true, (ready, end, previous, None))?;
            self.schedule(v, a)?;
        } else {
            self.service(v, s, ready, previous)?;
        }
        Ok(())
    }
    fn service(
        &mut self,
        v: &Admitted,
        s: usize,
        ready: u64,
        previous: Option<usize>,
    ) -> Result<()> {
        let p = self.sequences[s].phases[self.sequences[s].step].clone();
        if p.name == "dma_issue" {
            let engine = self.sequences[s].engine.expect("DMA issue engine");
            if !self.pending_issue.entry(engine).or_default().remove(&s) {
                return Err(refuse("InternalError", "", "issue without reservation"));
            }
            self.inflight.entry(engine).or_default().insert(s);
            self.sequences[s].issue = Some(self.now);
        }
        self.sequences[s].service_ready = false;
        self.sequences[s].active = true;
        let (end, ratio) = if p.name == "channel_service" {
            let lo = self
                .channels
                .get(&p.owner)
                .copied()
                .unwrap_or(Ratio::integer(0))
                .max_integer(ready)?;
            let hi = lo.plus(Ratio::new(
                v.hardware.channel_step_num,
                v.hardware.channel_step_den,
            )?)?;
            self.channels.insert(p.owner, hi);
            (hi.ceil()?, Some((lo, hi)))
        } else if p.name.ends_with("_noc") && !p.occupies {
            (self.now, None)
        } else {
            (
                edge(
                    v.hardware.freq[p.domain.expect("clocked service")],
                    self.now,
                    p.cycles,
                )?,
                None,
            )
        };
        let a = self.activity(v, s, p, false, (ready, end, previous, ratio))?;
        self.schedule(v, a)
    }
    fn schedule(&mut self, v: &Admitted, a: usize) -> Result<()> {
        let end = self.activities[a].end;
        if end == self.now {
            self.finish(v, a, None)?;
        } else {
            self.wheel
                .schedule(
                    end,
                    0,
                    u32::try_from(self.activities[a].phase.owner).map_err(|_| overflow())?,
                    endpoint(&self.activities[a], true),
                    u32::try_from(a).map_err(|_| overflow())?,
                )
                .map_err(|_| refuse("InternalError", "", "component completion schedule"))?;
            self.pending_count += 1;
            self.max_live_events = self.max_live_events.max(self.pending_count);
        }
        Ok(())
    }
    fn finish(&mut self, v: &Admitted, a: usize, queued: Option<Event>) -> Result<()> {
        let ordinal = self.event(a, true, queued)?;
        self.activities[a].completion = ordinal;
        let s = self.activities[a].sequence;
        if self.activities[a].alignment {
            self.sequences[s].service_ready = true;
            self.sequences[s].active = false;
            self.sequences[s].ready = self.now;
            return Ok(());
        }
        let p = self.activities[a].phase.clone();
        if matches!(p.name, "read_port" | "write_port" | "channel_service") {
            self.busy.remove(&p.owner);
            self.last.insert(p.owner, a);
        }
        self.sequences[s].step += 1;
        self.sequences[s].active = false;
        self.sequences[s].ready = self.now;
        if self.sequences[s].step < self.sequences[s].phases.len() {
            return Ok(());
        }
        self.sequences[s].end = Some(self.now);
        // Terminal transitions can release a credit or complete a dependency.
        // A phase-0 batch coalesces before reserve; inline completion is seen next loop.
        self.eligibility_dirty = true;
        if let Some(engine) = self.sequences[s].engine {
            self.inflight
                .get_mut(&engine)
                .expect("acquired credit")
                .remove(&s);
        }
        let j = self.sequences[s].job;
        let mut c = Counts::default();
        match &v.graph.jobs[j].kind {
            TaskKind::Compute { m, k, n, .. } => {
                self.busy.remove(&p.owner);
                self.last.insert(p.owner, a);
                c.mac = mul(*m, mul(*k, *n)?)?;
                c.issued = mul(2, mul(*m, 256 * 256)?)?;
                c.sram_read = mul(2, add(mul(*m, *k)?, mul(*k, *n)?)?)?;
                c.sram_write = mul(2, mul(*m, *n)?)?;
                self.jobs[j].useful = mul(c.mac, 2)?;
                self.jobs[j].issued = c.issued;
            }
            TaskKind::Dma { write, .. } => {
                if *write {
                    c.write = self.sequences[s].payload;
                    c.write_txn = 256;
                    c.sram_read = c.write;
                } else {
                    c.read = self.sequences[s].payload;
                    c.read_txn = 256;
                    c.sram_write = c.read;
                }
            }
            TaskKind::Unicast { .. } => {
                c.unicast = self.sequences[s].payload;
                c.sram_read = c.unicast;
                c.sram_write = c.unicast;
            }
            TaskKind::Barrier => {}
        }
        self.counts.merge(&c)?;
        self.per_job[j].merge(&c)?;
        if self.jobs[j]
            .sequences
            .iter()
            .all(|&x| self.sequences[x].end.is_some())
        {
            self.jobs[j].end = Some(self.now);
            for (i, b) in v.graph.buffers.iter().enumerate() {
                if !b.persistent
                    && !b.consumers.is_empty()
                    && b.consumers.iter().all(|&u| self.jobs[u].end.is_some())
                {
                    self.allocations[i].end.get_or_insert(self.now);
                }
            }
        }
        Ok(())
    }
    fn ready_jobs(&mut self, v: &Admitted) {
        for j in 0..self.jobs.len() {
            if self.jobs[j].ready.is_none() {
                let before: Vec<_> = v
                    .graph
                    .dependencies
                    .iter()
                    .filter(|(_, b)| *b == j)
                    .map(|(a, _)| *a)
                    .collect();
                if before.iter().all(|&a| self.jobs[a].end.is_some()) {
                    let ready = before
                        .iter()
                        .map(|&a| self.jobs[a].end.unwrap())
                        .max()
                        .unwrap_or(0);
                    self.jobs[j].ready = Some(ready);
                    for &s in &self.jobs[j].sequences {
                        self.sequences[s].enabled = true;
                        self.sequences[s].ready = ready;
                    }
                }
            }
        }
    }
    fn reserve(&mut self, v: &Admitted) -> Result<bool> {
        if !self.eligibility_dirty {
            return Ok(false);
        }
        self.eligibility_dirty = false;
        self.reservation_opportunities.push(ReservationOpportunity {
            time: self.now,
            event_cursor: self.events.len() as u64,
            granted: vec![],
        });
        let mut ready: Vec<_> = self
            .sequences
            .iter()
            .enumerate()
            .filter(|(_, s)| {
                s.enabled && s.issue.is_none() && s.reservation.is_none() && s.ready <= self.now
            })
            .map(|(i, s)| {
                (
                    s.ready,
                    s.engine.unwrap_or(0),
                    s.request.clone().unwrap_or_default(),
                    i,
                )
            })
            .collect();
        ready.sort();
        let mut changed = false;
        for (_, _, _, s) in ready {
            if let Some(engine) = self.sequences[s].engine {
                let acquired = self.inflight.get(&engine).map_or(0, BTreeSet::len);
                let pending = self.pending_issue.get(&engine).map_or(0, BTreeSet::len);
                if (acquired + pending) as u64 >= v.hardware.credit_limit {
                    continue;
                }
                // Strict eligibility uses reservation time, never the later aligned issue edge.
                // Equal job-readiness/release is dependency eligibility, not credit waiting.
                if self.now > self.jobs[self.sequences[s].job].ready.unwrap() {
                    let before: Vec<_> = self
                        .sequences
                        .iter()
                        .enumerate()
                        .filter(|(i, x)| {
                            *i != s
                                && x.engine == Some(engine)
                                && x.reservation.is_some_and(|t| t < self.now)
                                && x.end.is_none_or(|t| t >= self.now)
                        })
                        .collect();
                    if before.len() as u64 == v.hardware.credit_limit {
                        self.sequences[s].credit_causes = before
                            .iter()
                            .filter(|(_, x)| {
                                x.issue.is_some_and(|t| t < self.now) && x.end == Some(self.now)
                            })
                            .filter_map(|(_, x)| x.activities.last().copied())
                            .collect();
                    }
                }
                self.pending_issue.entry(engine).or_default().insert(s);
                self.sequences[s].reservation = Some(self.now);
                self.reservation_opportunities
                    .last_mut()
                    .expect("actual opportunity")
                    .granted
                    .push(s);
            } else {
                self.sequences[s].issue = Some(self.now);
                self.sequences[s].ready = self.now;
            }
            changed = true;
        }
        Ok(changed)
    }
    fn issue(&mut self, v: &Admitted) -> Result<bool> {
        if self.observations == ObservationVersion::V3 {
            return self.reserve(v);
        }
        let mut ready: Vec<_> = self
            .sequences
            .iter()
            .enumerate()
            .filter(|(_, s)| s.enabled && s.issue.is_none())
            .map(|(i, s)| {
                (
                    s.ready,
                    s.engine.unwrap_or(0),
                    s.request.clone().unwrap_or_default(),
                    i,
                )
            })
            .collect();
        ready.sort();
        let mut changed = false;
        for (_, _, _, s) in ready {
            let engine = self.sequences[s].engine;
            let at = if engine.is_some() {
                edge(v.hardware.freq[0], self.sequences[s].ready, 0)?
            } else {
                self.sequences[s].ready
            };
            if at > self.now {
                continue;
            }
            if let Some(engine) = engine {
                let live = self.inflight.entry(engine).or_default();
                if live.len() as u64 >= v.hardware.credit_limit {
                    continue;
                }
                // Credit evidence records occupants just before this timestamp, not an arbitrary old request.
                if self.now > self.jobs[self.sequences[s].job].ready.unwrap() {
                    let before: Vec<_> = self
                        .sequences
                        .iter()
                        .enumerate()
                        .filter(|(i, x)| {
                            *i != s
                                && x.engine == Some(engine)
                                && x.issue.is_some_and(|t| t < self.now)
                                && x.end.is_none_or(|t| t >= self.now)
                        })
                        .collect();
                    if before.len() as u64 == v.hardware.credit_limit {
                        self.sequences[s].credit_causes = before
                            .iter()
                            .filter(|(_, x)| x.end == Some(self.now))
                            .filter_map(|(_, x)| x.activities.last().copied())
                            .collect();
                    }
                }
                self.inflight.entry(engine).or_default().insert(s);
            }
            self.sequences[s].issue = Some(self.now);
            self.sequences[s].ready = self.now;
            changed = true;
        }
        Ok(changed)
    }
    fn run(mut self, v: &Admitted) -> Result<Self> {
        loop {
            while let Some(event) = self.wheel.peek() {
                if event.t_ps != self.now {
                    break;
                }
                let event = self.wheel.pop().expect("peeked event");
                self.pending_count -= 1;
                self.finish(v, event.payload as usize, Some(event))?;
            }
            self.wheel
                .enter_inline_phase(self.now)
                .map_err(|_| refuse("InternalError", "", "component ready phase"))?;
            loop {
                self.ready_jobs(v);
                let issued = self.issue(v)?;
                let mut ready: Vec<_> = self
                    .sequences
                    .iter()
                    .enumerate()
                    .filter(|(_, s)| {
                        (s.issue.is_some() || s.reservation.is_some())
                            && s.end.is_none()
                            && !s.active
                            && s.ready <= self.now
                    })
                    .map(|(i, s)| {
                        (
                            s.ready,
                            s.engine.unwrap_or(0),
                            s.request
                                .clone()
                                .unwrap_or_else(|| v.graph.jobs[s.job].id.clone()),
                            i,
                        )
                    })
                    .collect();
                ready.sort();
                // Resolve every uncontended crossing before same-time FIFO acquisitions.
                let selected = ready
                    .iter()
                    .find(|(_, _, _, s)| {
                        self.sequences[*s].service_ready
                            || !self.sequences[*s].phases[self.sequences[*s].step].contended
                    })
                    .or_else(|| {
                        ready.iter().find(|(_, _, _, s)| {
                            !self.busy.contains_key(
                                &self.sequences[*s].phases[self.sequences[*s].step].owner,
                            )
                        })
                    })
                    .map(|x| x.3);
                if let Some(s) = selected {
                    if self.sequences[s].service_ready {
                        self.service(v, s, self.sequences[s].ready, None)?;
                    } else {
                        self.start(v, s)?;
                    }
                } else if !issued {
                    break;
                }
            }
            if self.jobs.iter().all(|j| j.end.is_some()) {
                self.duration = self.now;
                break;
            }
            let wake = self
                .sequences
                .iter()
                .filter(|s| s.enabled && s.issue.is_none() && s.engine.is_some())
                .filter_map(|s| edge(v.hardware.freq[0], s.ready, 0).ok())
                .filter(|&t| t > self.now)
                .min();
            self.now = match (self.wheel.peek().map(|e| e.t_ps), wake) {
                (Some(a), Some(b)) => a.min(b),
                (Some(a), None) => a,
                (None, Some(b)) => b,
                _ => {
                    return Err(refuse(
                        "IncompleteExecution",
                        "",
                        "no runnable component transition",
                    ));
                }
            };
        }
        Ok(self)
    }
}
pub(crate) fn execute(input: &str, trust: &Trust) -> Result<Value> {
    execute_with_observations(input, trust, ObservationVersion::V2)
}

#[cfg(test)]
mod kernel_tests {
    use super::*;
    #[test]
    fn positive_hop_zero_cycles_still_has_receiving_alignment() {
        let all: Value =
            serde_json::from_str(include_str!("../testdata/synthetic-component-jobs.json"))
                .unwrap();
        let v = &all["D10-read"];
        let trust = Trust {
            registry: v["registry"]["registry_hash"].as_str().unwrap().into(),
            profiles: BTreeMap::from([(
                v["profile"]["profile_hash"].as_str().unwrap().into(),
                BTreeSet::from([v["admission"]["case_id"].as_str().unwrap().into()]),
            )]),
            engine: v["engine"].clone(),
        };
        let mut admitted =
            component_admission::validate(&crate::wire::canonical(v).unwrap(), &trust).unwrap();
        // Private typed-state probe, not a rehashed/authorized mapped job or a result carrier.
        admitted.hardware.hop_cycles = 0;
        let state = Runtime::new(&admitted).unwrap().run(&admitted).unwrap();
        let phases: Vec<_> = state
            .activities
            .iter()
            .filter(|a| a.phase.name.ends_with("_noc"))
            .collect();
        assert_eq!(phases.len(), 4);
        assert_eq!(phases.iter().filter(|a| a.alignment).count(), 2);
        assert!(
            phases
                .iter()
                .filter(|a| !a.alignment)
                .all(|a| a.phase.occupies)
        );
    }
}

// PRIVATE UNAPPLIED prototype seam; public protocol does not select this version.
pub(crate) fn execute_with_observations(
    input: &str,
    trust: &Trust,
    version: ObservationVersion,
) -> Result<Value> {
    let v = match version {
        ObservationVersion::V2 => component_admission::validate(input, trust)?,
        ObservationVersion::V3 => component_admission::validate_model(
            input,
            trust,
            component_admission::ModelVersion::Two,
        )?,
    };
    let expected = if version == ObservationVersion::V3 {
        "2"
    } else {
        "1"
    };
    if v.raw["engine"]["model"]["name"] != "native-intervals"
        || v.raw["engine"]["model"]["version"] != expected
    {
        return Err(refuse(
            "UnsupportedFidelity",
            "/engine/model",
            "explicit observation/model version",
        ));
    }
    let state = match version {
        ObservationVersion::V2 => Runtime::new(&v)?,
        ObservationVersion::V3 => Runtime::new_version(&v, version)?,
    };
    let runtime = state.run(&v)?;
    crate::component_accounting::construct(&v, &runtime)
}
#[cfg(test)]
#[path = "issue_proposal_tests.rs"]
mod issue_proposal_tests;
