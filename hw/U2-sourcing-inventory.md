# U2 active hardware input status

H1/H2 and U0004 are accepted under
[U2-B1-decision-v1](../docs/reviews/U2-B1-acceptance-record.md).
This index records the current disposition; the complete original leaf/source inventory is
preserved unchanged in
[the B1 input snapshot](../docs/reviews/U2-inputs/B1-05daf76bfda1/hw/U2-sourcing-inventory.md).

## Accepted stipulated designs

- designs/npu-l4.yaml: SHA256
  `41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0`;
  all 59 sourced stipulations and categorical settings accepted.
- designs/npu-m256.yaml: SHA256
  `e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e`;
  all 67 sourced stipulations and categorical settings accepted.

Values are design conditions, not measured facts. Preserve consumed source paths, rationales
and conditions in derivation/export/report. No engine may tune them to fit a nominal oracle.
Nominal efficiency1.0 is a separately identified assumption; energy remains unverified.

## Incomplete references remain review-only

The TPU v5e and Blackhole p100a YAMLs exist only in preserved B1 review inputs. They are not
installed under active hw/references/. Their positive numeric stand-ins and unsupported
categories are not estimates. No physical runs, performance reporting or L3 use is approved.
Loader-only tests must be named as such and select the explicit review fixture.

The original inventory records live vendor sources and capacity/clock/layout qualifications.
Those missing facts remain open. Before executable reference use, obtain reviewed replacements
or a separately reviewed fidelity limitation for every consumed unknown.
This is a file-specific draft restriction, not a ban on all genuine stub-backed predictions.

Actual H1 export, pinned bridge execution and human v2 generation/adoption now have
committed records in [v2 adoption execution](../docs/reviews/U2-adoption-v2-execution/README.md).
The approved inputs and original generation identities remain unchanged. Stage 2
source corrections require coordinator reconciliation and a later source/input freeze
where applicable; see [B response](../docs/reviews/U2-publication-history.md#b-documentation-correction). Neither
adoption nor complete analytic report capture establishes hardware/model validation.
Independent review, remaining acceptance cases and sprint closure remain separate.
