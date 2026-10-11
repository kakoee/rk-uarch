# rk-uarch

rk-uarch estimates one AI accelerator's work for an LLM inference iteration. U2
implements a stateless analytic engine, saved-input replay, characterization tables
and provenance-aware reports. Each row describes one chip's shard across all layers,
without inter-chip collectives. Predictions remain STUB: reproducibility and verified
provenance do not establish silicon accuracy, an error band or verified energy.

## Quickstart

```sh
uv sync --extra dev
uv run uarch validate hw/designs/npu-l4.yaml
uv run uarch table --help
uv run uarch report --help
```

To produce a table and report, follow the [public workflow](docs/u2-workflow.md).
It prepares and captures a workload, drafts its source declarations, stops for actual
independent declaration reviews, then assembles the table context. The review step is
required; a bare hardware/model command is insufficient.

## Repo map

`contract/`: shared vocabulary; `hw/`: designs and references; `src/rkuarch/`:
preparation, engines, tables and reports; `native/`: later native engine work;
`validation/`: evidence; `measure/`: silicon kits; `docs/`: design and execution plan.

## Working here

Read [CLAUDE.md](CLAUDE.md), then [build-spec §0](docs/build-spec.md).
See [how it works](docs/how-it-works.md), the [accepted U2 design](docs/u2-design.md)
and [execution plan](docs/execution-plan.md). U2 software review acceptance is scoped;
artifact refresh, the public demonstration and publication exits remain separate.
