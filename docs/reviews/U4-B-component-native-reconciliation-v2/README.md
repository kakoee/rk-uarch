# B follow-up limited to remaining gaps

The completed handoff at0e9996a remains authoritative for B's executed evidence on A's
source64837bea3724919facbc27be1c7f5644a6354cfa and handoff
e5291669fbfa27028a0ae1d1b258b6778d24fadd. No selected execution, build, final-source check,
archive publication, authority or protected installation was repeated in this follow-up.
This addendum reports only new diagnostic detail and unresolved contract distinctions.

## Exact construction trace gaps

[read-gaps.json](read-gaps.json) binds the unchanged raw construction receipt and all
three remaining parser gaps:

- `debug.trace.450`, line11: `???() = ?`, followed by exit0.
- `debug.trace.452`, line9: `???() = ?`, followed by exit0.
- `release.trace.482`, line10: unfinished `sched_getaffinity(482, 32, ...)`, followed
  by exit0 without a resumed result.

The known-record diagnostic inventories230313 records from1030 debug process logs and
216813 records from910 release logs. Every observed child has a trace and every trace
has a terminal record. Among parseable records there are zero unresolved FD/path records
and no child execution mentioning diagnostic inputs. Both modes include76 pinned-source
paths and1319 pinned-cache paths. These are observed path counts, not unique semantic
inputs or an exhaustive dependency claim. Dynamic/OS/generated inputs remain separately
classified, including the inherited CLONE_FS/cwd and transient-content limitations.

The new diagnostic recipe reuses the original path classifier/walker on known records;
it does not alter raw traces or the original strict parser. Every trace was checked
against its original build-receipt hash before analysis. The full diagnostic inventories
remain private at `/tmp/u4-b-component-read-gaps-01/{debug,release}.json`, bound by hashes
in the published summary. The unknown debug syscalls cannot be assumed harmless or
reclassified as known non-file operations. The release gap is a known affinity query,
but its completion outcome is missing. Strict read closure remains unaccepted. A later
review must explicitly accept this bounded evidence or request a narrowly justified new
capture; no retry build was launched here.

## Remaining issue-reservation contract distinctions

The existing cap1/cap2, read/write and333 ps issue-gap evidence is reused. Pending
reservations are coherent as internal capacity bookkeeping if acquired plus pending
never exceeds the per-engine limit, conversion is atomic, and reservations create neither
inflight credit nor occupied payload-port time. Three additional boundary expectations
make the unresolved causal rule precise for an engine whose existing credit releases
at60000 ps on a1GHz core:

| Dependency ready | Reservation/alignment start | Issue | Tight causes at alignment start |
| --- | --- | --- | --- |
| 59999 | 60000 | 60000 | releasing credit only |
| 60000 | 60000 | 60000 | dependency only under the installed strict-wait predicate |
| 60001 | 60001 | 61000 | dependency only; release60000 is not tight |

These are synthetic proposal expectations, not native outputs or human L1 workings.
Phase0 release must precede phase2 eligibility at60000. The installed rule in
`validation/component/transition_checks.py:112` requires issue_ps strictly greater than
job ready_ps before credit can be an eligible cause; native component.rs uses the same
strict test. Therefore the middle row must not gain a credit predecessor merely because
its endpoint is tight. A broader all-tight-credit rule would be a deliberate contract
change, not a harmless observation addition. Complete-cause checking requires all
**eligible** tight causes, and eligibility is the decision that must be frozen. Alignment
removal, early acquisition, an extra credit cause in either the middle or last row, or a
false finite issue-rate delay each has a distinct expected failure. A zero-length alignment in the
first two rows still needs an exact versioned inventory/endpoints decision; it must not
be omitted merely because its duration is zero.

The remaining contract decision is concrete: define separate unreserved waiting,
reserved/alignment and acquired/inflight populations; exact same-time endpoint ordering;
and whether new alignment changes job-start/allocation endpoints. Read/write phases,
per-engine ownership, all-ready same-edge issue and independent engine credit pools must
retain their installed timing laws. These choices require the reviewed observation
version/schema/checker proposal already identified in0e9996a. Nothing here installs it.
