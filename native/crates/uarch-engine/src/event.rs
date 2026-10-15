use crate::Error;
use std::{cmp::Reverse, collections::BinaryHeap};

#[repr(u16)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    TaskReady,
    ComputeDone,
    DmaIssue,
    DmaDone,
    NocHead,
    NocTail,
    MemReq,
    MemResp,
    MemTick,
    SyncArrive,
    BarrierRelease,
    StatSample,
    End,
    DependencyReady,
    OwnerGrant,
}
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Event {
    pub t_ps: u64,
    pub seq: u64,
    pub target: u32,
    pub kind: u16,
    pub phase: u8,
    pub flags: u8,
    pub payload: u32,
    pub pad: u32,
}
const _: () = assert!(std::mem::size_of::<Event>() == 32);
impl Event {
    pub fn new(t_ps: u64, seq: u64, target: u32, kind: Kind, phase: u8, payload: u32) -> Self {
        Self {
            t_ps,
            seq,
            target,
            kind: kind as u16,
            phase,
            flags: 0,
            payload,
            pad: 0,
        }
    }
    pub fn key(&self) -> (u64, u8, u32, u64) {
        (self.t_ps, self.phase, self.target, self.seq)
    }
}
/// Handles never escape the queue. Removal returns the slot to the free list.
#[derive(Debug, Default)]
pub struct Arena {
    slots: Vec<Option<Event>>,
    free: Vec<usize>,
}
impl Arena {
    pub fn insert(&mut self, event: Event) -> usize {
        if let Some(id) = self.free.pop() {
            self.slots[id] = Some(event);
            id
        } else {
            self.slots.push(Some(event));
            self.slots.len() - 1
        }
    }
    pub fn remove(&mut self, id: usize) -> Option<Event> {
        let e = self.slots.get_mut(id)?.take()?;
        self.free.push(id);
        Some(e)
    }
    pub fn capacity_slots(&self) -> usize {
        self.slots.len()
    }
}
type Entry = Reverse<((u64, u8, u32, u64), usize)>;
const SLOTS: u64 = 4096;
/// Two 4096-slot levels; upper slots span 4096 lower slots. Heap holds overflow.
/// Slot heaps retain allocation and order ties by the complete event key.
#[derive(Debug)]
pub struct Wheel {
    width_ps: u64,
    now_ps: u64,
    last_key: Option<(u64, u8, u32, u64)>,
    phase_floor: u8,
    seq: u64,
    arena: Arena,
    near: Vec<BinaryHeap<Entry>>,
    far: Vec<BinaryHeap<Entry>>,
    overflow: BinaryHeap<Entry>,
    promoted: u64,
}
impl Wheel {
    pub fn new(max_freq_hz: u64) -> Result<Self, Error> {
        if max_freq_hz == 0 {
            return Err(Error::InvalidClock);
        }
        Ok(Self {
            width_ps: (1_000_000_000_000 / max_freq_hz).max(1),
            now_ps: 0,
            last_key: None,
            phase_floor: 0,
            seq: 0,
            arena: Arena::default(),
            near: (0..SLOTS).map(|_| BinaryHeap::new()).collect(),
            far: (0..SLOTS).map(|_| BinaryHeap::new()).collect(),
            overflow: BinaryHeap::new(),
            promoted: 0,
        })
    }
    fn place(&mut self, entry: Entry) {
        let tick = entry.0.0.0 / self.width_ps;
        let base = self.now_ps / self.width_ps;
        // Compare block numbers, avoiding time multiplication and u64 horizon overflow.
        if tick / SLOTS == base / SLOTS {
            self.near[(tick % SLOTS) as usize].push(entry);
        } else if tick / (SLOTS * SLOTS) == base / (SLOTS * SLOTS) {
            self.far[((tick / SLOTS) % SLOTS) as usize].push(entry);
        } else {
            self.overflow.push(entry);
        }
    }
    pub fn schedule(
        &mut self,
        t_ps: u64,
        phase: u8,
        target: u32,
        kind: Kind,
        payload: u32,
    ) -> Result<u64, Error> {
        if phase > 3 {
            return Err(Error::InvalidEvent);
        }
        if t_ps < self.now_ps
            || (t_ps == self.now_ps && phase < self.phase_floor)
            || self
                .last_key
                .is_some_and(|key| (t_ps, phase, target, self.seq) < key)
        {
            return Err(Error::PastEvent);
        }
        let seq = self.seq;
        self.seq = self.seq.checked_add(1).ok_or(Error::SequenceOverflow)?;
        let event = Event::new(t_ps, seq, target, kind, phase, payload);
        let id = self.arena.insert(event);
        self.place(Reverse((event.key(), id)));
        Ok(seq)
    }
    /// Enter the accepted inline phase only after all queued earlier phases drain.
    pub(crate) fn enter_inline_phase(&mut self, t_ps: u64) -> Result<(), Error> {
        if t_ps < self.now_ps
            || (t_ps == self.now_ps && self.phase_floor > 2)
            || self.peek().is_some_and(|e| e.t_ps <= t_ps && e.phase < 2)
        {
            return Err(Error::PastEvent);
        }
        self.now_ps = t_ps;
        self.phase_floor = 2;
        Ok(())
    }
    /// An inline closure message is not inserted into the wheel. Its target may
    /// decrease as canonical owner selection restarts; time/phase may not regress.
    pub(crate) fn inline_event(
        &mut self,
        target: u32,
        kind: Kind,
        payload: u32,
    ) -> Result<Event, Error> {
        if self.phase_floor != 2 {
            return Err(Error::InvalidEvent);
        }
        let seq = self.seq;
        self.seq = self.seq.checked_add(1).ok_or(Error::SequenceOverflow)?;
        Ok(Event::new(self.now_ps, seq, target, kind, 2, payload))
    }
    fn minimum(&self) -> Option<Entry> {
        self.near
            .iter()
            .chain(self.far.iter())
            .filter_map(|h| h.peek().copied())
            .chain(self.overflow.peek().copied())
            .max()
    }
    pub fn peek(&self) -> Option<Event> {
        let id = self.minimum()?.0.1;
        self.arena.slots[id]
    }
    pub fn pop(&mut self) -> Option<Event> {
        let entry = self.minimum()?;
        self.now_ps = entry.0.0.0;
        self.last_key = Some(entry.0.0);
        self.phase_floor = entry.0.0.1;
        let base = self.now_ps / self.width_ps;
        // Move overflow into the current upper window, then upper slots into lower.
        while self
            .overflow
            .peek()
            .is_some_and(|e| e.0.0.0 / self.width_ps / (SLOTS * SLOTS) == base / (SLOTS * SLOTS))
        {
            let e = self.overflow.pop().expect("peeked entry");
            self.promoted += 1;
            self.place(e);
        }
        let slot = ((base / SLOTS) % SLOTS) as usize;
        while let Some(e) = self.far[slot].pop() {
            self.promoted += 1;
            self.place(e);
        }
        let removed = self.near[(base % SLOTS) as usize]
            .pop()
            .expect("minimum promoted");
        debug_assert_eq!(removed, entry);
        self.arena.remove(removed.0.1)
    }
    pub fn level_counts(&self) -> (usize, usize, usize) {
        (
            self.near.iter().map(|v| v.len()).sum(),
            self.far.iter().map(|v| v.len()).sum(),
            self.overflow.len(),
        )
    }
    pub fn promotions(&self) -> u64 {
        self.promoted
    }
    pub fn arena_slots(&self) -> usize {
        self.arena.capacity_slots()
    }
}
