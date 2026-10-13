# U3 bounded plan-and-prompt amendment

Prepared for Javid on 2026-10-12 after approval to incorporate the independent review
and coordinator response. **This package is the exact proposed amendment, not a live
plan installation or a release to implement the native engine.**

- [Exact 24-path patch](plan.patch)
- [Proposed U0023](proposed-U0023.md)
- [Changed paths, before/after hashes and checks](review.json)
- [Guarded human installer](human-install.sh)
- [Independent review](../U3-post-fork-plan-review-v1/README.md)
- [Coordinator response](../U3-post-fork-plan-review-v1/coordinator-response.md)
- [Separate artifact-dependency audit proposal](../U3-artifact-dependency-repair-proposal-v1/README.md)

Baseline: `afb35022971e56703fe35104b818b8a226c039d7`. Only Markdown changes are in the
patch: the plan, build-spec and synchronized prompts; CLAUDE/README instructions; U0005's
prospective supersession pointer and new U0023; the shipped rk-sim boundary draft/prompt.
No actual rk-sim repository file is changed or approved by this package.

## What the amended plan says

| Milestone | Concrete purpose |
| --- | --- |
| U3 / G2 | Accept the bounded design and task boundaries; schedule remaining checks by their first consumer |
| U4a | Mapped interface M; internal kernel K1 may overlap it; public wiring K2 follows approved schema; then bounded models B |
| U4b / G3a | Extend and verify the actual reference benchmark scope R, including usable TPU representation and native admission; no unrelated full grid |
| U5 / G4 | Frozen-prediction TPU campaign, after readiness and hardware authorization |
| U6 / G5 | Expanded mesh qualification at representative points, diagnostics, integrated regression, controlled-host performance and real nightly |
| U7 / G6 + G3b | Deeper mechanisms and first full product tables for declared study/demo consumers; required precision/input decisions first |
| U8 / G7 | Blackhole campaign after explicit reference/measurement/native readiness |
| U9 | Existing conditional parallelism/scaling work |
| U10 / G9 | Actual rk-sim integration, requiring eligible C2 tables and explicit rejection of lower/inconsistent composites |
| U11 | Existing hardening and recorded campaign/product obligations |

**Passing silicon is not required to produce tables.** A full table does not validate
an engine. Small tables or direct execution results may be used earlier for concrete tests
and consumers. If reference access/feasibility delays U5, its gate stays open while
independently ready native/product work may proceed. No sprint is falsely closed.

U7's npu-m256/70B/FP8/tp8 demo remains required. This amendment moves, rather than resolves,
the relevant precision/RoPE, ragged composition, hardware and public-contract decisions.
Native workload expansion needed for that product is explicit in U-P7 T; a bounded GEMM
or TPU-specific admission is insufficient. No hidden BF16 substitution or dropped work.

## Review disposition coverage

| Finding | Concrete proposed change |
| --- | --- |
| PF-01 | G3a reference-suite readiness separated from G3b consumed-table readiness |
| PF-02 | Hardware/precision/ragged decisions required at their actual consumer, not before unrelated silicon |
| PF-03 | U-P5/U-P8 source/representability work; U-P11b R admission before U-P9; equivalent readiness before U-P15 |
| PF-04 | U10 requires G6 + G3b; P18 and boundary draft reject non-C2/inconsistent detail |
| PF-05 | Separate dependency-audit/migration proposal; U0002 and code remain unchanged |
| PF-06 | Correctness Linux CI separated from controlled-host performance; real nightly by G5; prospective cold-clone rule |
| PF-07 | K1 internals can overlap M; K2 public protocol waits for approved carriers |
| PF-08 | Attribution qualified before use; G4 allocation is an investigation heuristic, not proof of causation |
| PF-09 | U6 removes full C1 mesh grid; expanded-scope qualification and integrated regression retained |
| PF-10 | U-P6 case-by-case consumer/deadline disposition; no blanket waiver or retrospective pass |
| PF-11 | Small test-only conformance task; actual vendored code distinguished from adapter scaffolding and later integration |
| PF-12 | Physical feedback no longer waits on an unused grid; independent verification remains useful and distinct |
| PF-13 | Explicit M/T, K1/K2 and B/R phases with scoped entry/exit; restricted vision read removed |
| PF-14 | Declared study/scale points where sufficient; point/table adapter and consumer coverage explicitly tested |

The response's qualifications are preserved: no blanket A-proposal approval; no invented
TPU fields; no automatic artifact generation; no pilot authorization; no claim that a
conformance adapter is production integration; and no interpretation of a budget ceiling
as a measured runtime. Optional matched tt-npe evidence follows U0005's optional-reference
rule rather than becoming another compulsory tool dependency.

## What remains separate

- Exact component/model assumptions, mapped schemas, toolchain/licenses and later semantic
  extensions still require their own concrete review. New U0023 does not install them.
- Hardware access, performance allocation, runner registration and paid measurements.
- Artifact-policy repair: audit first, then an exact protected-policy/enforcement proposal
  and human migration. Current strict-support checks still apply meanwhile.
- Runtime implementation, source freezes, generation/adoption, native qualification,
  publication and sprint closure.

U0005's original text is retained with a pointer to prospective U0023 supersession. Other
accepted ADRs are unchanged. G4 numerical thresholds and G7/G8 blocks are preserved; G4's
attribution wording clarifies inference rather than changing its 70% allocation rule.
No new performance or effort forecast is invented; revised tasks need re-estimation.

## Verification

Executed on a private export with the proposed patch:

- Prompt-sync tests: **4 passed**, including both shipped rk-sim prompt mirrors.
- Strict vendor check: passed; all **97 bound support paths byte-identical** to baseline.
- Exact reconstruction: applying the patch to a second baseline export reproduces all
  **24 changed paths** byte for byte.
- Patch whitespace; Markdown-only scope; preserved U0005 original text and G7/G8 blocks.

The existing environment's Python was used directly; no `uv sync`, install or build ran.
No full suite, native build, measurement or independent review of this exact patch is
claimed. The earlier independent report reviewed the plan, not this amendment's bytes.

## Installation and Git boundaries

The package and review records can be committed as ordinary documentation. Protected
installation is a separate human step. The installer checks the exact package commit,
patch digest, base/target identities and clean index; uses normal hooks; never pushes.

Read-only preflight from the primary repository:

```bash
bash docs/reviews/U3-plan-amendment-v1/human-install.sh --check
```

After the package is committed and its exact commit has been reviewed, the human command is:

```bash
UARCH_HUMAN=1 bash docs/reviews/U3-plan-amendment-v1/human-install.sh --commit <PACKAGE_COMMIT>
```

Do not paste the placeholder literally. The coordinator supplies the actual package commit.
The helper creates one local protected documentation commit and stops. Push remains separate.
If the baseline or selected paths drift, reconcile and review a revised package; do not
override the guard or rewrite other lane work.
