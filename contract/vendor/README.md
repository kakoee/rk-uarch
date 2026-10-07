# vendor — reviewed rk-sim snapshots

A human generates a complete staging candidate using `make vendor-rk SHA=<sha> RK=<path>`.
After review, a human may adopt the complete candidate following U0002's artifact-revision
procedure. Ordinary generator reruns refuse differing output at an occupied destination.
Never edit generated files by hand, including metadata or oracle values.

Each `rk-sim@<sha>/` contains:

- `MANIFEST.json`: pin and SHA256 inventory of every other file.
- `GENERATOR.json`: historical generator/oracle fingerprints; revised generation also records
  the verified oracle environment. Strict compatibility requires current fingerprints.
- `uv.lock`: revised snapshots retain the pinned upstream lock for environment verification;
  legacy candidates lack it and cannot pass the revised strict check.
- `schema.json`: upstream generated schema bundle.
- `rk/`: unchanged source closure of the mirrored carriers, loaded only in tests.
- `components/`: exact required and optional PARAMS component inputs.
- `model_shapes/`: model/shape sidecars with immutable source attribution.
- `parity/fixtures.json`: rk-sim `iteration_cost()` oracle records.
- `parity/refusals.json`: actual unsupported-precision refusals captured during generation.

`--check` checks integrity, coverage, contract pin and current compatibility; `--check
--historical` checks integrity and recorded identity only and cannot certify current
compatibility or adoption. Neither checks whether an artifact has been published.
Production code never imports these files. Harness self-tests are not U2 workload parity.

Generation removes file write bits as a local precaution. Git does not preserve these
bits: checkouts normally restore mode 0644. Manifest checks and human artifact review are
the integrity controls. Javid approved this interpretation of the prompt's read-only requirement
in the Stage 2 response; complete ADR acceptance remains pending. See U0002 for staging, review and adoption;
see U0019 for preparation/replay ownership (U0003 owns later prepared-input schemas).
