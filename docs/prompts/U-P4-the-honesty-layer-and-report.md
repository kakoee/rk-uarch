# U-P4 · U2 · Lane B — The honesty layer, and the report every number renders through

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{provenance,report}/README.md, build-spec §2.6 (badges)
and §2.7 (the validation ladder), contract/uarch_contract/{sourced,model_card,table}.py.
From rk-sim READ-ONLY: rk/provenance.py (combine), docs/decisions/0009, 0011 §5.4, 0021,
0027, docs/glossary.md §2, web/src/components/Badged.tsx (the rule you are porting).

TASK: provenance/ decides what a number may claim. report/ is the only way a number reaches
a human. Develop both against contract/tests/fixtures/toy_table.json; you do not need
U-P3 to have landed.

1. provenance/badge.py — badge_for(row_or_metric, spec, model_card) -> (Calibration,
   conditional_on[]). The rules, exactly as build-spec §2.6 states them:
   a. WORST OF CONTRIBUTORS, over claims only. Stipulations are EXCLUDED from the
      calculation and RECORDED in conditional_on. A stipulation neither lowers nor raises a
      badge; it scopes the question.
   b. THE MODEL IS A CONTRIBUTOR. Its rung comes from the model card, which comes from the
      ledger. L0–L2 evidence -> stub. L3 -> estimated, scoped. L4 -> measured.
      spec_derived never applies to a model.
   c. THE CEILING: anything computed for a design_status: proposed spec is capped at
      estimated, whatever its evidence. Enforced in code, with a test.
   d. combine([]) is stub, as in rk-sim: a number that cannot name what fed it has no
      evidence behind it.
   e. NOTHING HERE MAY RAISE A BADGE. Write a test that fuzzes inputs and asserts the output
      badge is never better than the worst claim contributor and never better than the model
      card's rung.
2. provenance/model_card.py — build a ModelCard from (engine id, engine version,
   fidelity_detail, mapping policy, ledger entries). validated_error_band is None unless
   ledger entries whose scope covers this request (family, op class, precision, shape regime,
   load regime, mapping match) supply it. None renders as "unknown". energy_verification is
   None until every coefficient family an energy figure uses has an L2 reference (deferred
   until after U8), and None renders energy as "unverified".
3. provenance/applicability.py — rk-sim ADR 0021's shape for uarch: for a request, which
   evidence dimensions MATCH, MISMATCH or are UNKNOWN (architecture family, op class,
   precision, shape regime, load regime, mapping match), using the bins ADR U0001 fixed, and
   judged where U0001 says (proposal: per row, with every operator in the row covered).
   Precision matches by format name: BLOCKFP8 evidence does not cover fp8 unless U0001 says
   why it should. A model card whose evidence does not apply to this
   request contributes stub for this request, whatever its best rung elsewhere.
4. report/ — `uarch report <table>` writes a self-contained static HTML file (plus a
   Markdown twin for agents), with no JavaScript framework and no network fetches:
   - every number renders through report/badged.py::badged(value, unit, badge,
     conditional_on, error_band). A raw float in a template is a build failure: add a
     template lint that fails on any {{ x }} whose x is not a Badged object;
   - "conditional: if built as specified (N stipulations)" with the list expandable;
   - error band shown as the band, or "unknown", NEVER "±0";
   - the fidelity chip (composite plus the per-subsystem detail), the model card, the
     measured interpolation and composition errors, and the flop-parity deviations;
   - a diagnostics section: a null diagnostic renders "not modelled", never 0 and never a
     blank that reads as zero;
   - a per-op roofline as static inline SVG (operational intensity against achieved
     throughput, from the table's counts; no JavaScript);
   - all four measured errors (interpolation, composition, layer reuse, cold vs steady), the
     initial state and the KV layout;
   - energy marked "unverified" while the model card's energy_verification is None;
   - a one-paragraph "what this table does not claim" generated from omissions (the declared
     ones included), warnings, stubs and the badge ceiling.

ACCEPTANCE TESTS (write first):
1. A stipulation does not lower a badge; a stub claim does; both appear in the right list.
2. L0–L2-only card -> the model contributes stub; L3 in-scope -> estimated; L3 out-of-scope
   for this request -> stub, with the mismatched dimension named.
3. Ceiling: a proposed design with an L4 card is capped at estimated, and the report says why.
4. Error unknown: a card with validated_error_band=None renders "unknown", and the rendered
   HTML contains no "±0" anywhere (grep test).
5. Template lint catches an injected raw {{ row.duration_s }}.
6. The report for the toy table is byte-identical across two runs (no timestamps in the
   body; the generation time goes in a comment block excluded from the hash).
7. A null diagnostic renders "not modelled": no diagnostic that is null in the toy table
   appears as 0 in the rendered report.
8. Precision scope: an fp8 request against BLOCKFP8-only evidence gets stub, naming precision.
9. Energy renders "unverified" when energy_verification is None, and stays "unverified" when
   only one coefficient family has a reference.
10. Applicability per row: a row with one operator whose shape regime the evidence does not
    cover gets stub, naming that operator.

GUARDRAILS: Do not read from an engine or compute a physical number here. Do not compute
error bars from a deterministic run; a deterministic simulator has no replication variance,
and a zero-width interval is the most confident error bar you could draw on the least-
validated number. No web app: the rk-sim UI is the interactive surface (U-P20).

ADR: docs/decisions/U0004-stipulated-values-and-the-estimated-ceiling.md. Say in plain words
that a chip which does not exist is never badged better than ESTIMATED, and that this will be
commercially uncomfortable, and that it is the thesis applied without exceptions.
```
