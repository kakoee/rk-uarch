# Component B — installation identity reconciliation and O2 evidence

This package completes B's author preparation for CI-C1 and
`B-U4-OBS2-TRANSIENT-LIFETIME-01`. It is an **unapplied proposal** for coordinator
reconciliation. The same reviewer's accepted Stage 3/F5 verdict is inherited and unchanged.
No implementation law, parser, engine or profile promise is changed by this delta. Human P2/NoC choices and protected installation remain pending.

## CI-C1: exact installation identity transition

The original selection test failed in the exact coordinator preview: the historical
whole-ADR hash `4f7a90b2…` differed from reconciled `edf565f9…`. The baseline failure is
retained in the evidence archive. The historical selection remains byte-identical, with
all 106 rows and all case/input bindings unchanged.

The proposed identity test retains its `candidate_files` assertion and historical mapping,
fixture, source and test checks. It obtains the **explicit prospective** postimages from
`validation/component/installation-binding.json`. Only two historical paths have replacements:

| Path | Historical reviewed identity | Proposed installation identity |
| --- | --- | --- |
| U0011 ADR | `4f7a90b201c0425a9906d746e4235ec4df362c15ffe91138f827edf2529f6140` | `edf565f9094c524b280888feaf29bcecc63b176aa573393c136b3494c7c640fd` |
| `test_stage2_selection.py` | `b7fb959ee27df2542c8bb60e13b3932a1218257e28610bc603d980da1d167d95` | Exact new hash in [transition.json](transition.json) |

The helper requires exactly those replacement paths and exactly the five added verification
paths, including the accepted F5 test. All other historical candidate identities stay fixed.
The reconciled ADR hash is an exact constant, not a current-file hash adopted at runtime.
Missing paths, extra overrides, F5 omission and arbitrary ADR changes fail.

The ADR is exactly the **32,221-byte installed text** followed by the **16,073-byte reviewed
component suffix**. The installed text and old reviewed ADR share the same 28,596-byte
historical prefix. Both streams are proved independently by exact byte/hash comparison:

- Installed text SHA-256: `afae0ebea7dfdfe761ec76ae374a35441db989f866a4ca4f5c29f0169a49e69b`.
- Reviewed component suffix SHA-256: `ad9b5369073403fa8a881a04e628db620c89f21d66ec062e90c3bc753c7eadba`.

Tamper controls alter each stream, omit the component suffix, drop the installed K2 suffix,
append later text, alter/omit F5 or the changed identity test, and alter the transition inventory.
The corrected identity selection passes all 15 tests. Private removal of each stream guard
makes its direct tamper test fail with `DID NOT RAISE`; removal of the postimage assertion makes
all four F5/self-test edit/omission controls fail. Exact bytes were restored and affected tests
rerun. These are **identity discriminators**, not behavioral checker kills. The full inventory
also hashes the helper, so a helper edit would independently fail the ordinary identity test;
the direct guard experiments do not claim to bypass that external/file integrity defense.

There is no self-hash cycle: the externally pinned [postimage manifest](postimages.json) binds
the installed binding record, and that record binds the helper and every changed/new test,
including the identity tests themselves. No test embeds the record's hash. The record does
not authenticate itself; its root must be pinned by the reviewed proposal/publication. Neither
record nor test confers execution trust or authority.

Later component changes require a **new prospective transition and externally pinned proposal**,
with explicit path pre/postimages, appropriate tests and review of any expanded transition set.
They must not mutate historical selections, accepted patches, reports or receipts. This narrow
record cannot accept arbitrary later code changes simply by rehashing the current tree.

## O2: actual transient @2 lifetime branch

[Obligation disposition](obligation-disposition.json) supplies the named B evidence. The new
helper builds a genuinely synthetic `/2`, mapping-`@2` carrier with five resident 3×5×7 bf16
tiles on one matrix owner. Real job admission and `validate_result` accept the valid carrier;
B's independent `check_v2` accepts it too. It is not C02's persistent accumulator: the shared
84-byte accumulator at offset 256 has producer `b` and terminal consumers **both `c` and `d`**.

Independent arithmetic per tile: 32 overhead cycles; staging `ceil((30+70)/1024)=1`;
wave `510+3=513`; drain `ceil(42/1024)=1`. At 1 GHz, each tile takes **547000 ps**.
The explicitly supplied order and dependency/resource causes give:

| Job | Dependency-ready ps | Service span ps |
| --- | ---: | --- |
| a, warm-up | 0 | [0, 547000) |
| b, producer | 547000 | [547000, 1094000) |
| c, first final consumer | 1094000 | [1094000, 1641000) |
| d, second final consumer | 1094000 | [1641000, 2188000) |
| e, tail | 2188000 | [2188000, 2735000) |

Job d's matrix wait is represented separately from service. The exact shared allocation is
**[547000, 2188000)**: producer start through the maximum of both final-consumer endpoints.
It starts after zero and ends before makespan. Warm-up and tail accumulators occupy disjoint
addresses, so deliberately extending this lifetime does not trigger a masking alias refusal.

Useful work is `5 × 2 × 3 × 5 × 7 = 1050` operations; issued work is
`5 × 2 × 3 × 256 × 256 = 1966080`. SRAM traffic is 500 read bytes and 210 write bytes;
HBM traffic is zero. The negative carriers preserve the complete result except one allocation
endpoint and its integrity seal; work, traffic, clocks, jobs, consumers and causal joins stay
truthful. All profiles/engine/build markers are synthetic unit anchors, never real execution
identities or authority.

| Negative | Structural result validator | Independent checker | Single-guard evidence |
| --- | --- | --- | --- |
| Allocate at 0 instead of 547000 | Admits | `accumulator lifetime mechanism` | Removing only that guard admits; regression `DID NOT RAISE` |
| Free at 2735000 instead of 2188000 | Admits | Same | Same |
| `free_ps=null`, meaning run end | Admits | Same | Same |
| Free at first consumer end 1641000 | Admits | `allocation access lifetime` | Removing endpoint guard still refuses here; removing access guard instead refuses at `accumulator lifetime mechanism` |

The endpoint guard is essential for the three overlong lifetimes. The early-free case shows
precise overlapping defenses, not global redundancy and not another unsafe-acceptance kill.
The five-test O2 selection passes intact and after exact restoration; endpoint removal gives
three failures with `DID NOT RAISE` and two passes. No semantic/model defect was found, and no
production correction is proposed. No human L1 working is fabricated.

## Exact proposal and reconstruction

[Postimages](postimages.json) and [transition](transition.json) bind:

- Base: `350c581f44a2e23c9b83e06e5667650a610b8d14`.
- Coordinator preview: `a960bc1099e8ee263351c0cf05b1264aef465185a2c83a45c603cbf42da836ad`.
- Six-path verification [delta](joins.unapplied.patch): `af055995c3896b827d7bdd6a6c2419b7bbcdd27a38422be06a9c84cbabe83465`.
- Full 29-path [combined proposal](install-with-joins.unapplied.patch): `008dc61147431cc6be3d78656a482512e17fd6d0f84a6beaf0920fe1bf641b70`.

The delta changes one existing identity test and adds the identity helper/tests/binding data
and O2 helper/tests. All 23 other preview postimages, including the reconciled ADR, remain
exact. The original accepted patches and all older proposal/review packages are untouched.

Using the pinned existing Python 3.12 environment, choose **one** route into a new private
export; both routes were executed and verified to identical 29 postimages:

```sh
PY=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
$PY -I -B docs/reviews/U4-B-component-install-joins-v1/reconstruct.py /tmp/component-install-joins
# Equivalent route: coordinator preview first, then B's delta, in another new directory:
$PY -I -B docs/reviews/U4-B-component-install-joins-v1/reconstruct.py /tmp/component-install-joins-ordered --ordered
```

Reconstruction checks preimages, postimages, nine activation inputs, the original first-use
sidecar, the immutable selection, and reverse application. It never applies to live main.
`isolated.py PRIVATE_EXPORT pytest ...` supplies explicit root/config and verifies all loaded
project module origins. `fault_controls.py PRIVATE_EXPORT NEW_LOG_DIR` reproduces only the
five focused guard experiments and affected restorations; it does not run a broad sweep.

## Executed checks, inherited evidence and boundaries

The **one final combined affected run passed 24 tests**: the 15 CI identity tests, five O2
tests, accepted F5 pair, historical selection join and existing C02 persistent positive.
Ordinary discovery with the existing CI filter collected **2407/2684 tests**, 277 deselected;
all 19 newly added nodes are present. Applicable lint, strict types for the five changed/new
Python files and exact reconstruction/hash checks pass. [Checks](checks.json),
[restoration](restoration.json) and the [evidence manifest](evidence-manifest.json) distinguish
these runs and retain the [logs](evidence.tar.gz). Development fixture/setup mistakes are
recorded separately and never counted as discrimination.
Two preparation helpers received string-line formatting after execution; [helper-formatting.json](helper-formatting.json) proves identical ASTs and string values. The archive preserves both exact executed and published helper bytes; no unchanged experiment was repeated.

Inherited without rerun: accepted Stage 3/F5/F6 outcomes, broad 488 selection, prior guard
sweeps, unchanged-source schema/import/support/vendor checks, and K2 execution evidence.
No F6 repetition, full suite, native build/run or CI polling occurred. [Publication checks](publication-check.json) distinguish literal patch-context whitespace
from the clean postimage bytes. Identity counts are not behavioral scores; overlapping development/final test counts are not additive.

O2's author evidence is supplied for coordinator reconciliation; the original pending receipt
remains historical. Human P2/NoC decisions, protected installation, actual L1 workings,
distinct future component runtime identities/authority and reference readiness remain separate.
No sealed K2 root or authority was touched, no artifact generation/adoption or U0024 change was
performed, and no qualification, G3a or U4 closure is claimed. This package stops at coordinator
reconciliation; it supplies no new independent-review verdict.
