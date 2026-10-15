# Current dependency audit

Subject and exact starting HEAD: `9b1408437b6dc08d9b77848f5fffe56c0cf1db72`.
The requested ancestor is this same commit. Main was integrated normally from `09a3a27`.
Installed U0024 is present and hashed in [inputs.json](inputs.json); remote native CI,
runner/registry/credential work remains deferred. No infrastructure was inspected or changed.

The original M patch SHA256 is
`d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`; selected repair SHA256 is
`c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
Both apply unchanged to a Git export of this HEAD. All 26 M postimages match A's published
`package.json`. The repair's six postimages were independently reconstructed from its
previously audited `f58e07828fa7a953b06800b227b948d7e9e71a88` preimages and match the current
combined export. There is **no current patch conflict or reconciliation delta**.
[selection.json](selection.json) records exactly 32 targets, absent/new preimages as null,
and full before/after SHA256s; no copied source tree or replacement patch is supplied.

The newly measured selected closure has **56 entries**; broad enumeration of the combined
source has **101**. [inventory.json](inventory.json) is the necessary source-support record;
[closure-delta.json](closure-delta.json) compares the previous final audit at `95c1774...`:
zero additions, removals or digest changes. This is a measured result, not a count invariant.
All reached files bind complete bytes, including function-local/conditional imports.

The actual M imports are recorded in [import-reads.json](import-reads.json). `mapped.py`
imports `assumptions`, `common`, `hardware`, `hashing`, `prepared`, `rotary_v2`, `table`,
Pydantic and stdlib fractions/typing/math. The added assumptions edge reaches an existing
retained file. M remains a direct-import leaf; there is no new reverse edge from nominal
staging roots or existing initializers to M. The three modified pre-existing files are
only `scripts/__init__.py`, `scripts/u2_inputs.py` and `scripts/vendor_rk.py`; the M patch
changes no existing initializer, hash dispatcher, hardware exporter or analytic engine.

The selected roots are `scripts/u2_inputs.py`, `scripts/vendor_rk.py`, `scripts/u2_support.py`.
The repair retains all scripts Python, parent/reserved initializers, `pyproject.toml`,
`uv.lock`, `hw/designs/npu-l4.yaml`, component-precision and two execution declarations,
`contract/tests/fixtures/u2_b/a2-export/{*.json,*.yaml,PIN}`, model-shape JSON and the complete
pinned historical-provenance family. `uarch_contract`, scripts, rkuarch/hw/engines and reserved
tests initializers are accounted for. The unchanged `prepared` local comparison import
remains included. The full modified vendor fingerprint is
`b82ae570dee99466389d609051425c501022d1ebf2efb03a2bc67a27a27c1b76`; embedded oracle program is
unchanged at `bca579505e96e3f105d4442e7b6c52c3cbe87316edde3ea896692abceb90993b`.

Non-import reads are distinct from nominal support:

| Consumer | Actual read or supplied input | Current boundary |
| --- | --- | --- |
| M admission | Explicit bundle, full hardware/assumptions, registry/profile and separately held expected hashes | No file, environment, network or dynamic-import read in `mapped.py` |
| Dedicated M schema checker | `contract/schema/mapped/*.json`, 12 roots | All exact postimages checked; no existing generator is changed |
| M tests | 11 mapped fixtures, canonical vectors and schema mirrors | Test inputs; no native result or human authority |
| Test-only `runpy` | Literal `contract/tests/rotary_v2_cases.py`; that helper reads its own bytes and the existing independent v1 bundle | Existing stdlib/hash helper, not a workload producer or oracle; outside nominal staging |
| B D02/D14 tests | Existing review-package bundles, profiles, registry and literal arithmetic helper | Proposals with test anchors; not installed production hardware or authority |
| Future saved-input/native consumers | Actual Git acceptance record, registry/profile/spec files, resolver/mapper/build/runner reads | Not implemented by this patch; audit at their actual first-use release |

No exclusion or policy change is needed for these inspected bytes. Static analysis remains
conservative, and explicit data-family registration, trusted CPython startup and absence of
concurrent source writes remain premises. An unexecuted future loader is not covered by a
promise that its closure will remain 56.

Live strict currentness passes, and the read-only current-adoption positive verifies the
actual 1,008-row/four-refusal artifact and its existing U3 human-review join. The current
manifest is `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.
The combined proposed source correctly exits 1 with `input support inventory changed`
against that artifact. No historical-mode fallback is used to claim compatibility.
The source-only installation must therefore remain local until the separate human lifecycle
produces and adopts a compatible pair.
