# U4-M-policy-freeze-generation-v1

**Proposed; awaiting Javid's exact freeze acceptance and human generation authorization.**
The previous approval covered input staging only; that human step succeeded and is audited.

Accept this exact source/input freeze and authorize two separate human generator process
invocations, using the reviewed locked environment and one new candidate output:

| Binding | Exact value |
| --- | --- |
| Source S | `0cf24d91eeca5cc45182eb6fb03202677fd97dcb` |
| Source tree | `275bcefbe616a049aa6d0a968ff81b5728f0563d` |
| Frozen input SHA256SUMS | `368c7e44dedd8586f2957f9e27030ce61573d3b9675f2f0df27e70c111abf32a` |
| Upstream rk-sim | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` |
| Whole generator script | `b82ae570dee99466389d609051425c501022d1ebf03a2bc67a27a27c1b76` |
| Embedded oracle program | `bca579505e96e3f105d4442e7b6c52c3cbe87316edde3ea896692abceb90993b` |
| Policy | `uarch-input-support/2` / `generator-imports-and-data/1` |
| Output root | `/home/jjaff/AI-infra-simulation/rk-uarch/tables/U4-M-policy-generation-v1` |

[freeze.json](freeze.json) binds the complete 56-file dependency inventory, exact input and
receipt locations/hashes, all observed source/oracle package versions and locks, uv version
and output identity. The source and upstream checkouts must remain unchanged. Output is
outside both checkouts, outside frozen inputs, absent before execution and never overwritten.

All 22 existing input data files are byte-identical to the currently adopted pair. Only
`support-policy.json` is added and `support-files.json` plus `SHA256SUMS` change. This is the
reviewed dependency-policy migration, not a workload or numerical reference change. The
inventory changes 97→56 through 17 additions, 58 removals and three changed shared scripts;
counts alone are not acceptance. Exact paths/digests and added provenance dependencies were
verified against the accepted audited closure. The complete new input set contains 25 files.

The human wrapper runs the unchanged installed generator twice against the same saved inputs:
first `created`, then `verified-identical`. The expected candidate count is 49 (the prior 48
plus the new policy input file), but only executed output can establish that result. It verifies
manifests, strict new-policy support, generator/environment identities and identical manifest
digests after both runs, then stops with the candidate and receipts intact.

The separate pristine upstream and external oracle environment were checked read-only:
CPython 3.12.14, NumPy 2.5.2, upstream lock
`d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c`.
Its package inventory matches the locked base selection via offline check. Staging/source
NumPy 2.5.3 is separately recorded and is not substituted for the oracle environment.
No dependencies are installed by either helper.

This approval does not adopt the candidate, rewrite any old provenance, change current test
bindings, commit/push A's source, authorize K2, or resume infrastructure. After generation,
the coordinator must audit every nominal query/count/duration/null and the four real refusals
against the old pair. Numerical changes are expected to be zero, not assumed. Adoption and
its new review/test bindings require a separate exact decision. No physical/native/silicon
validation is established by nominal oracle equality.

A's current source stays local until the complete compatible source/artifact tip passes its
integration checks. The K1 reviewer continues independently. Existing U0002 human generation
rules and U0024 infrastructure deferral remain operative.
