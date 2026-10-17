//! Native mechanics and fixed-delay JSON boundary. Host first-use authority is external.
#![forbid(unsafe_code)]
#![deny(clippy::disallowed_types)]

mod event;
mod simulation;
mod time;
mod topology;
pub use event::{Arena, Event, Kind, Wheel};
pub use simulation::{Action, Delay, Job, Outcome, Owners, Simulation};
pub use time::next_edge;
pub use topology::{Direction, Topology};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    InvalidClock,
    TimeOverflow,
    SequenceOverflow,
    PastEvent,
    ForeignOwner,
    InvalidOwner,
    DuplicateJob,
    MissingDependency,
    DuplicateDependency,
    DependencyCycle,
    InvalidEvent,
    InvalidRoute,
    Serialization,
}

#[cfg(test)]
mod tests;

#[cfg(test)]
mod stage2_tests;

#[cfg(test)]
mod release_tests;

mod carrier;
mod wire;

mod admission;
mod hardware;

mod accounting;

pub mod protocol;
pub use carrier::Refusal;

#[cfg(test)]
mod peer_dto_tests;

mod component;
mod component_accounting;
mod component_admission;
#[cfg(test)]
mod component_admission_tests;
#[cfg(test)]
mod component_tests;
