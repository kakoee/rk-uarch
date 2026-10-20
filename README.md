# rk-uarch


**Ordinary native transition:** the `/4` component interface below is implemented in the
U4 basic-provenance proposal. It awaits focused independent review and human installation
of the complete protected/source patch; it is not a U4 closure or shipping approval.

Run an already prepared supported component job with the installed package and executable:

```sh
python -m rkuarch.engines.native.ordinary run --job job.json --executable /path/to/uarch-engine --output result.json
python -m rkuarch.engines.native.ordinary replay --job job.json --output result.json
```

The executable itself uses ordinary EOF JSON I/O:
`uarch-engine --protocol uarch-engine/4 < job.json > result.json`.
Fixture hardware requires `--test-only` in either interface and remains verification-only.
Production component hardware/model restrictions, cold initialization, exact sync and the
corrected model version 2 / observations 3 remain. Historical `/3` jobs are explicitly
refused by this executable; sealed historical K2 results and executables are unchanged.

Python callers use `rkuarch.workload.ordinary.prepare_bundle` and `prepare_job` for existing
mapped points, then `rkuarch.engines.native.ordinary.run` or `replay`. No mapping producer
runs during saved-job execution or replay. Input/output files carry software, engine and
model versions plus existing content hashes. No executable/source hashes, profile case
inventory, host selector, build archive, review file or custom startup loader is required.
Runtime dependencies are Python 3.12+, the installed wheel and its locked declared
libraries, the native binary and its system loader/libraries, and input files. Replay
needs only the Python installation and saved job/result. The wheel contains the ordinary
schemas and independent model-law checkers; tests and development reviews are unnecessary.

The normal user-controlled Python installation is the boundary. A-F3 is **retired by scope
change**, not passed or repaired. B-PROV-STAGING-01 and historical trace/container findings
remain historical findings in the retired system. Human L1, the affected historical `/2`
restriction, U0024, U4b/reference/G3a and independent-review obligations remain.


rk-uarch estimates one AI accelerator's work for an LLM inference iteration. U2
implements a stateless analytic engine, saved-input replay, characterization tables
and provenance-aware reports. Each row describes one chip's shard across all layers,
without inter-chip collectives. Predictions remain STUB: reproducibility and verified
provenance do not establish silicon accuracy, an error band or verified energy.

Current version/replay limit: `/4` accepts package version `0.0.1` only, without a local
build identifier, and both run and replay require that installed version. It does not
distinguish builds. Engine `native-stage/2` and model `native-intervals/2` identify the
implemented semantics. A package version change requires a protected contract change and
an explicit compatibility decision at that time; cross-version replay is not supported.
Fixture admission also requires 32-cycle job overhead and 32-cycle barrier latency,
the values supported by the independent checker. Other values refuse as `UnsupportedHardware`.

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
