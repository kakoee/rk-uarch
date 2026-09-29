# NNNN — Admit characterized C2 tables for `compute_resource`, and stipulated values for proposed designs

**Status:** DRAFT — for both founders. Take the next free number at adoption. · **Lane:** both
(schema + documents) · **Companions:** ADR 0002, 0009, 0011, 0016, 0021, 0026, 0027; rk-uarch
ADR U0001 (the integration contract) at the contract version named below.

**Touches `rk/schema/`, `rk/provenance.py`, `CLAUDE.md` and build-spec §1.3.** So it is a
boundary change: one schema PR, both founders approve, landing **before** P18 and P19 start.
That is the same shape as ADR 0011's schema PR.

---

## Context

rk-uarch produces **characterization tables**: for one proposed or reference chip, the
per-iteration cost of one tensor-parallel shard over a grid of (batch, context) points, with its
own fidelity detail, measured interpolation and composition errors, and a model card saying what
evidence stands behind it. The contract is rk-uarch's `uarch-contract/<MAJOR.MINOR>`.

Two things in rk-sim currently refuse this, correctly:

1. **Build-spec §1.3** rules out "C1+/M1+/N1+ fidelity of any kind" and "surrogate/memoization
   acceleration engines". A characterization table is both a C2 answer and a memoized one.
2. **`SourcedValue`** has no way to say "this is a design choice, not a claim about the world".
   A proposed chip's parameters would have to be badged `stub`, which makes every custom-silicon
   answer look like a placeholder, or better than `stub`, which would be a lie.

## Decision

### 1 · Admit exactly one thing into §1.3

A `compute_resource` may run at **C2** when, and only when, it carries a characterization
table conforming to `uarch-contract/<MAJOR>`. Nothing else on §1.3's out-of-scope list moves:
no C1 anywhere, no M1+ or N1+, no online co-simulation, no uarch import. rk-sim **reads files**.

### 2 · The schema PR

1. `rk/provenance.py`: `SourcedValue` gains `kind: Literal["claim","stipulation"] = "claim"` and
   `rationale: str | None`. A stipulation requires `provenance=None`, `source=None`,
   `date=None` and a non-empty `rationale`; a claim forbids `rationale`. `Metric` gains
   `conditional_on: tuple[str, ...] = ()`. `combine()` is unchanged. Callers pass claims
   only, and a new `split_claims()` returns `(claims, stipulation_ids)`, so the
   worst-of rule is untouched and no badge can be raised by this change.
2. `rk/schema/fidelity.py`: `IMPLEMENTED["compute"]` gains `C2` (admissible). Whether it is
   **built** for a component stays the registry's answer (ADR 0016).
3. `rk/schema/components.py`: `ComponentDescriptor` gains
   `design_status: Literal["shipping","proposed"] = "shipping"` and
   `characterization: Characterization | None`, where
   `Characterization = {table_path, table_hash, spec_hash, contract_version}`. The loader
   refuses a stipulation on a `shipping` component.
4. `rk/schema/results.py`: `FidelityMapEntry` gains optional `model_origin`, `fidelity_detail`
   and `table_hash`.
5. `rk/schema/characterization.py`: the table models, adopted from rk-uarch's contract at the
   named version. **From this PR, rk-sim's schema is the source of truth for the contract** and
   rk-uarch vendors it back. The truth moves once, deliberately.

`config_hash` moves once for every system, because new optional fields dump as `null`. ADR
0011 recorded the same effect and the same reason not to suppress it with `exclude_none`.

### 3 · The rules the engine must follow

These are rk-uarch ADR U0001's six rules, restated as rk-sim obligations. P18 tests each one.

1. A row is one shard, so the table-backed cost uses a **tp divisor of 1**, and collectives
   stay rk-sim's.
2. Canonical compositions; the table's measured composition error is surfaced as a warning.
3. The envelope is checked at build time; extrapolation is refused.
4. DVFS uses the table's frequency axis. DVFS without one is a hard error.
5. Counts use rk-sim's channel names. Extension channels are carried as "unmodelled".
6. The component's params equal `derive_rk_params` of the cited spec, checked by hash.

### 4 · Badges

The uarch model is a named contributor whose badge is the table's model-card badge.
Stipulations are excluded from worst-of and recorded in `conditional_on`. A `proposed`
component is capped at `estimated`. Fidelity still never moves a badge (ADR 0011 §5.4).

### 5 · Human-owned text, applied by the founders in the PR

- CLAUDE.md invariant 1's scope note gains: *"A stipulation is a design choice on a
  `proposed` component; it is not a claim, carries a rationale instead of a source, and never
  enters worst-of."*
- Build-spec §1.3's ASIC row reads: *"Custom ASIC placeholder: STUB, or C2 from a
  characterized table (rk-uarch)"*.

## What this does not do

It does not admit C1, M1+ or N1+. It does not let rk-sim call rk-uarch. It does not
change R0, R1, any existing golden, or any existing metric's value. It does not add an API
route: the model card rides in existing responses. It does not settle operator vocabulary for
P16. If P16 is taken, its operator list and rk-uarch's `operators.py` should be reconciled in
P16's own boundary ADR.
