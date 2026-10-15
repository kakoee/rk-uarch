# Installed observations and proposed delta review

Installed source418d697 retains mapped.py SHA256
`3b7587633f70e14ec2a195f80539f6c9cf74975938214f57df67d8441da39829`.
The executed carrier controls demonstrate that TASK_RELEASE, DEPENDENCY_READY and
OWNER_GRANT each refuse the installed enum, while an existing TASK_READY structural control
passes before/after. Queue clock_domain=None also refuses. These are synthetic structural
checks, never native output or permission to use a fictitious core domain.

A's published partial event patch from821dc90, SHA256
`6dd4ebdfd9c4e6be8a5c36ebc98cb117bfdbf745980827957aa0ba98c6c2c76c`, adds only
DEPENDENCY_READY and OWNER_GRANT to mapped.py and its two generated mirrors. It does not
resolve release, offset provenance, all-zero/tie semantics. The coordinator's A follow-up
requires the complete patch, mirrors and ADR proposal. At this package's initial source
pin418d697 that completed addendum was not published. No review of absent bytes is claimed;
see README/identity for any subsequent published-peer reconciliation.

| Observation/channel | Honest K2 representation / remaining check |
| --- | --- |
| Events | Must be genuinely dispatched events with original schedule sequence and actual observation ordinal, including real release and inline closure. Proposed three enum additions need protected acceptance; never translate grant into TASK_READY just to pass schema. |
| Jobs | Observed ready/grant/end, actual owner, all completions, tight blocking IDs. Synthetic fixed-delay work counts0 and op/group/tile null; no copied graph work. Required native instrumentation is pending. |
| Resource intervals | Observed positive occupancy union per owner; preserve zero ownership in jobs/events. No release-offset or queue waiting charged as busy. Every declared owner's busy total, including0, must be explicit. |
| Critical intervals | Derived only from actual tight ordered causes plus actual release evidence. S02/S12 discriminate offset/idle from occupancy. Installed category overhead alone does not type release vs service; exact completed proposal must define a machine-checkable mapping or narrow additional carrier delta. |
| Queue membership | Recommend installed **unrepresented**, reason fixed-delay owners lack physical queue domains. Ready/grant already support public FIFO/wait checks. This does not discharge V21/V24. A future non-clocked queue carrier would be another protected decision, not implicit core/noc/dram. |
| DMA/transfers/allocations | Unrepresented with explicit fixed-delay scope reasons; no empty fabricated physical observations. |
| Fidelity/energy/per-op | Null subsystem fidelity/diagnostics, energy unknown/unverified, empty per_op and null u_c0_duration. No model accuracy promotion. |
| Runtime metrics | Dispatch count and arena max-live must come from actual executor/wheel instrumentation. Capacity or total schedule count is not high-water occupancy. |
| Launch/error receipt | Operational executable origin/digest, status, stdout/stderr hashes, source/tool identity and actually measured host wall time. Not modeled picoseconds or deterministic engine output. |

For same-time dispatch, check actual phase progression and causal observation order, including
descending owner IDs in inline closure. Validate without reordering output. Trace on/off
must not govern whether mandatory observations exist. Schema acceptance cannot establish
tight causes, FIFO, genuine execution intervals or honest queue semantics by itself.
