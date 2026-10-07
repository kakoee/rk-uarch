# U2 kickoff obligations carried forward from accepted U1 reviews

Publication integration note, 2026-10-06, prepared by Lane B for Javid. This makes existing
obligations discoverable; it does not accept U0003, add semantics or implement U2. Read
[U0002](../decisions/U0002-the-vendored-snapshot-and-parity-discipline.md),
[accepted Lane B review](U1-lane-B-review.md) and
[accepted U0019](../decisions/U0019-standalone-preparation-and-prepared-input-replay.md)
when proposing U0003 and starting U-P3. G1 and U0003's prerequisite acceptance still apply.

| Item | Existing owner and required acceptance |
| --- | --- |
| B-F16, accepted deferral to U2 | U0003 author defines the component-precision interface; Lane B's vendor/parity maintainer owns matrix support; Lane A's U-P3 preparation/workload owner supplies the prepared/imported-bundle adapter. Require a BF16-only npu-l4 PARAMS fixture checked against its declared supported compute peak, with no substituted peak, and parity-adapter coverage of an actual prepared bundle under U0019. A generator change requires the reviewed human artifact-refresh lifecycle, even at the same upstream SHA. |
| Embedding accounting, unresolved U2 workload-parity obligation | Lane A's U-P3 workload owner exposes the actual graph/oracle difference, with Lane B's parity owner preserving attribution/reporting and Javid receiving the outstanding accounting/scope decision. U-P3 task 4 explicitly calls out embedding/lm_head differences; acceptance 3 requires workload graph parity. The approximately 6.54% nominal 8B embedding parameter share is not a measured operation/duration offset and must not be subtracted automatically. Keep nominal U1 inputs. Apply total absolute adjustments <=5% per fixture/channel and residual magnitude <=0.5%; no splitting, cancellation refund, dropped fixtures or widened tolerances. An ordinary over-budget difference remains failed. Unsupported classification requires a documented scope incompatibility; A-F12 does not grant an embedding exception. |
| A-F12, implemented and accepted interim policy | B's existing guard rejects uniform-/tp projections requiring replication/padding before calling the candidate and retains every fixture in coverage. A's legitimate request shapes remain supported by the contract. A component-aware projection is future reviewed U-P3 work, not a physical-correctness certification or permission to relabel workload results. |

U1 acceptance covers contract/harness/fixture evidence; it is not actual workload parity.
The embedding question is explicitly carried into U2, not silently treated as resolved.
Any changed public contract must follow the U0003 prerequisite and coordination with U-P4.
