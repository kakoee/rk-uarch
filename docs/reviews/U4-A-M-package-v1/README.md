# U4 A — exact M proposal, revision 1

Status: early bounded checkpoint for B's dependency audit; **not accepted or installed**.
Base: `f58e078` (U4 kickoff); published `u03-end` target
`6d39a234a14855c86ca54b795501a0b0b2618d7b` is an ancestor. All changes below exist only
in [protected.patch](protected.patch), validated in a disposable Git export. Live protected
files, oracle, artifact policy and engine remain unchanged. Git is the delivery mechanism.

The patch adds strict mapped bundle/point/TaskGraph/job/result, profile/registry, hardware
projection, count/traffic and observation carriers, a dedicated schema generator, five
input fixtures and admission tests. See [inventory.md](inventory.md) for B's concrete edges.
No native result fixture exists: a parser shape is not a completed behavioral case. The
input job's engine hashes are explicitly labeled unbuilt schema placeholders and must not
be used as an implementation receipt or frozen qualifying profile.

At this early checkpoint: 22 schema/prototype input tests pass; carrier mypy and focused
ruff pass. [tests-first.txt](tests-first.txt) records the initial missing-module failure
before implementation. Rehashed mutations exercise semantic checks, separately from stale
hash tests. R02/R03 full-model wrapping controls, richer closure/resource attacks, complete
legacy controls and result-observation laws are still being completed. This checkpoint is
usable for import/data auditing, not a claim that all M acceptance cases are finished.

Exact choices needing review include the hardware leaf projection, observation record keys,
job assumptions carrier, approval/signing mechanism and registry trust/bootstrap. These will
be disposed explicitly before the final handoff. B owns independent expected values/corpus
and CI; A owns carrier/model law; Javid owns protected acceptance and human lifecycle.
