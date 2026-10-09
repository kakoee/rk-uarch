# U0003 — One chip, one set of facts

**Status: PROPOSED.** Author: Lane A, 2026-10-07. Decision-maker: Javid
(@jjaffari), acting for both U2 lanes. No Reza approval is claimed.

Baseline: `1e9e794a84c5173812c23a1cf2fc04b85e6f6831`, clean `u2/analytic` at
entry; `u01-end^{commit}` equals HEAD. The annotated tag object is
`f26346f654f9b2c4a9626c9877e2922bfd720ea4`, not a conflicting commit.
This is an uncommitted design package, not implementation, adoption or publication.
U1/G1 and U0001/U0002/U0019/U0020 remain closed. The integration worktree's
U2-orchestration-kickoff.md supersedes historical pending-publication language.
Accepted U0021 already settles U2's fresh GitHub WSL2 clone plus same-published-commit
hosted Ubuntu CI; no renewed host approval is requested.

The proposed boundary is fully specified by this ADR and
[the review package](../reviews/U2-U0003-proposal/README.md), particularly
[interfaces](../reviews/U2-U0003-proposal/interfaces.md), the proposed JSON Schema,
synthetic JSON fixtures, [accounting investigation](../reviews/U2-U0003-proposal/accounting.md),
and [ownership/exits/estimates](../reviews/U2-U0003-proposal/delivery.md).
JSON Schema is structural; the named semantic rules in interfaces.md are equally normative.
All recommendations below need Javid's shared-baseline acceptance before either lane codes.

## Proposed decisions needing acceptance

| ID | Background and alternatives | Recommendation and tradeoff |
| --- | --- | --- |
| D1: versions | 0.1 has neither prepared inputs nor report-ready per-op data. Silently adding fields defeats extra-forbid readers; an implicit converter cannot recover missing provenance. | Introduce public `uarch-contract/0.2`, `uarch-prepared/1`, `uarch-engine/1`, `resolved-ops/1`, `uarch-report-context/2`. Keep historical 0.1 evidence parseable via explicit legacy inspection; refuse 0.1 for new execution/report verification. Future unknown prepared/protocol versions fail closed. This is an explicit capability refusal, not a change to U-P19's later major/minor reader policy. |
| D2: authoritative truth and projection | Pinned loader rejects extended claims as well as stipulations and requires an execution model and eligible citations. | Primary ComponentExport preserves spec/status/derivation and all extended values; a separately hash-bound five-field test projection records all losses and explicit model efficiency. Retained .55 unchanged; new synthetic npu-l4 1.0 requires acceptance. Complete metadata, KV check, full-loader probes and error boundaries are in comparison-evidence-export.md. |
| D3: report packaging | Full hardware contains cycles, which cannot be embedded indiscriminately in table results. Bare file references are unverifiable; entirely separate per-op results impede portable reports. | Table embeds per-op counts, roofline coordinates, complete scope and result identities. Hash-bound bundle/spec/card/derivation companions provide artifact validation. Deterministic CLI resolution is specified; missing/wrong artifacts refuse a verified report. HTML/Markdown are standalone after generation. Alternative: embed all artifacts in table, requiring a broader cycle exception and larger files. Do not broaden the accepted narrow cycle echo. |
| D4: transport/time | README allows a pure function; build-spec requires subprocess JSON and ps while U-P3 speaks of Row seconds. | One JSON subprocess boundary, reusable pure analytic core behind it. Nonnegative finite binary64 `duration_ps`, no integer-ps quantization for analytic; named ps_to_seconds conversion once in table/. Native may emit integer-valued ps later. Integer ceiling would preserve a floor but distort very short cases and summed per-op equality. |
| D5: stateless analytic scope | Priming and cold/steady experiments need a stateful model, which U-C0 lacks. Pretending to prime fabricates a measurement. | Carry exact state in coverage/identity, state_model=stateless_roofline; cold and steady may give equal numbers but remain separate inputs. All four experimental errors stay null/zero samples. Detailed state, mappings, schedules and error experiments remain later work. |
| D6: operator accounting | Parameter counts are not execution counts; norms, gather, fused attention, KV pages and intermediate DRAM accesses need concrete conventions. Last-token vs all-token lm_head, triangular vs full-square prefill, and full-page vs valid-token traffic differ. | `resolved-ops/1` spells out all counts below. Recommend all-token lm_head for standalone prefill, explicit full-square attention default (causal only when declared), valid-token reads within page-granular accesses, append-only KV writes. Gather uses explicit rank-local selected-token count, never a dense V×D matmul. No allocation padding is charged as valid work unless physically executed dimensions say so. Each is an explicit modelling assumption, not a hardware claim. |
| D7: conserved rank hits | tp2/M1 cannot execute one gather hit on both ranks simultaneously. | Require conserved supplied hit vectors. Representative mode requires equal physical work; narrowly add balanced_tp_selected_rank for unequal embedding hits only, with explicit synthetic high-level policy or supplied counts. This changes U0019 scope only if accepted. Imports remain authoritative; see two-track-amendment.md. |
| D8: selected S drafting direction | 8B count mismatches exceed budget; null/absent channels and .55 duration scope differ. Javid selected S for drafting only. | Propose two models: physical-resolved production engine with independent correctness/replay tests and complete discrepancy reports; test-only nominal-rk-compatibility candidate with unchanged count/duration thresholds against every adopted fixture. This replaces old physical gates; it does not satisfy them. Exact old/new exits, candidate isolation, U3 and U0021 scope amendments are in two-track-amendment.md and public-amendments.patch. No implementation or replacement gate is accepted. |
| D9: precision and comparison inventory | Generic Precision defaults admitted [{}]; upstream-only components have no uarch spec hash. | ComponentPrecision requires explicit unique compute/KV pairs and typed upstream-only or projection binding. Proposed 1008 successes/four direct-peak refusals; optional BF16/FP8 +144 only by explicit review. Preserve all fixtures and A-F12 before either comparison candidate. Full comparison artifacts bind raw actual/reference state and all identities. |
| D10: deterministic reporting | A live generation time in a hash-excluded comment still changes report bytes. | Omit wall-clock timestamps everywhere in canonical HTML/Markdown, including comments. Deterministic build/version identities are allowed. Alternative: fixed input timestamp, adding identity complexity without useful physics. |
| D12: DRAM frequency coverage | Clock domains can scale, but HardwareSpec has a single explicit bandwidth and no bandwidth-versus-clock curve. Guessing linear scaling may change a memory roof without evidence. | Refuse non-base frequency with a scalable DRAM domain in U2 until an explicit rule is accepted. Fixed DRAM domains support all positive core frequency ratios. Alternatives are constant declared bandwidth or a declared linear model; each admits more cases but adds an assumption. This is an engine capability limit, not removal of contract grid shapes. |
| D11: evidence closure and display | Band-less evidence, family and used metric contributors were unbound; empty claims were mistaken for a stub claim. | ReportContext/2 binds exact evidence/source/review/order/verification/registry/recipe/comparison closure. Family is report-only. Preserve purpose, granularity, precision roles, independent scopes and UNKNOWN. Empty claim summary=null, real stub claims preserved; model remains contributor. Default hide STUB magnitudes; explicit --show-unvalidated-predictions requires finite executed result, resolved contributors and STUB label on every surface. Visible-by-default remains an explicit alternative. |

No recommendation accepts itself. D8 requires a substantive accounting/exit disposition,
not just agreement on field names. D2's projection and D7's selected-rank extension also
need explicit review; do not hide them in a schema approval. The package intentionally
contains no new production fields, generator changes, oracle evidence or hardware designs.

## Consequences and acceptance boundary

One HardwareSpec remains the authority. B authors `hw/` and its sourcing inventory; A
implements derivation and consumes those files after acceptance. No hardware duplication.
Preparation resolves rank dimensions, fusion, padding, dependencies and multiplicities.
Engines may validate supported shapes; they may not regenerate, re-shard, re-fuse or replace
mapping. A supplied detailed TaskGraph is refused in U2, not downgraded to analytic.

Same captured bundle plus engine/version/run inputs gives identical table bytes, even with
the local producer removed. An independent producer may give identical numeric results but
has distinct producer provenance and therefore distinct bundle/request/table identities.
No identity claim authenticates an external author's truthfulness.

B receives sufficient results and artifacts to verify table/request/spec equality,
conditional_on path/value equality, card identity and complete per-row evidence scope.
Claims, model evidence and stipulated conditions remain separate. Proposed designs are
capped at estimated; L0–L2-only models remain stub; unknown errors never become zero.

Acceptance identifies baseline, exact ADR/package hashes, versions and exact ownership.
The coordinator reconciles B's independently authored counterexamples and records Javid's
decisions before phase 2. Two later fresh independent review loops, all U2 exits and U0021
published-revision validation still remain. This proposal is not a sprint closure.

## Revision 2 intake and acceptance record

C1–C5, D6/D7/D12, precision inventory and ownership dispositions are in
[amendment-dispositions.md](../reviews/U2-U0003-proposal/amendment-dispositions.md).
The preserved initial manifest is e67cfdae8b6eb3c030670640b0f8760cc541f9ed8bb5c3b223bdff998e078ee1;
changes-from-initial.json records file-level old/new hashes. Existing public documents are
untouched. public-amendments.patch is review text, including new U0001/U0002/U0019/U0021
addenda without rewriting their historical acceptance records. S drafting authorization is
not schema, model, scope, display, efficiency or gate acceptance.
