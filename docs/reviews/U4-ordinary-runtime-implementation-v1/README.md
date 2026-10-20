# U4 ordinary execution — consolidated implementation handoff

**Implementation proposal; complete transition unapplied.** The published default remains
historical until a human installs `transition.patch` as one coherent source/contract change.
This package is ready for focused independent review, not author-independent approval,
U4/G3a closure, a product campaign or shipping approval.

## Freeze and reconstruction

Implementation base: `669bdb0f7032e8955dbd0daaea059b733d4aa250`, inspected after the user's
pinned `da6ee495f30f9a98de2f2494efe32527e8d6e013`. The only intervening published commit is
the user's basic-provenance direction package; no uninspected peer source is incorporated.
The fresh independent clone is `/tmp/rk-uarch-simplify`; the coordinator and A/B clones
were not edited. Reza's `1d497be` is the intent reference, not a rollback target.

The exact source is carried by this package commit's [transition.patch](transition.patch),
with its [SHA-256](transition.sha256) and [reconstructed Git tree](source-tree.txt).
The package commit freezes the proposal source; it does **not** install that source on main.
The combined patch includes all source, generated schemas and protected ADR changes, so CI
on published main never imports an unapplied module. Historical formats, golden oracle files, `pyproject.toml` and `uv.lock` are unchanged.
The ordinary wheel configuration is in standard `hatch.toml`. The exact supplied `policy-and-plan.patch` was the starting proposal.
Synthetic smoke inputs are preserved in `smoke-inputs/`; their observed outputs are
`evidence/smoke-*-release.json`. They are new smoke evidence, not regenerated oracle data.

Reconstruct privately, without modifying the checkout:

```sh
python docs/reviews/U4-ordinary-runtime-implementation-v1/reconstruct.py /tmp/u4-review
```

`reconstruct.py` exports the recorded base, checks/applies the patch in the new directory,
and checks the complete source tree. It neither installs protected files in the working
checkout nor creates a runtime approval record. Human installation must carry the entire
transition together; do not cherry-pick only the new imports or schemas.

## Ordinary interface after installation

```sh
python -m rkuarch.engines.native.ordinary run --job job.json --executable /path/to/uarch-engine --output result.json
python -m rkuarch.engines.native.ordinary replay --job job.json --output result.json
# Direct binary transport: one EOF-delimited JSON request per process.
uarch-engine --protocol uarch-engine/4 < job.json > result.json
```

The Python API is `rkuarch.engines.native.ordinary.run(saved, executable=...)` and
`replay(saved, output)`. Both validate the saved inputs, full result bindings and observations,
and then run the packaged independent local-law checker. Replay imports no mapping/preparation
producer and needs no executable. `rkuarch.workload.ordinary.prepare_bundle` assembles an
existing mapped point; `prepare_job` selects it without remapping. The existing OpSpec,
TaskGraph, mapping versions, hardware laws and analytic engine remain.

Fixture hardware/work requires `--test-only` (Python `test_only=True`) and stays
`verification_only`. The production path uses the existing supported hardware, component
scope, cold initialization, ratio1 clocks, bf16, exact sync and current model restrictions.
No full-model/table scope or second engine was introduced. Exit 0 is complete canonical
stdout; semantic refusal is canonical stderr/status 2; other status/stream combinations
cannot become success. Input/output byte bounds, process deadlines and exact child-process
cleanup remain in the shared transport.

## Carrier and gate changes

| Previous ordinary-path prerequisite | Successor |
| --- | --- |
| Rust `protocol.rs::authority()`, generated ENGINE_JSON/TRUST_JSON and compiled case inventory | Shipping `/4` capability/schema admission; ordinary production binary tested without a fixture flag. Historical `/3` explicitly refused. |
| Implementation/compiler-lock hashes in engine/model identity and producer | Strict `/4` software identities: package `0.0.1`, engine `native-stage/2`, model `native-intervals` version `2`; producer name/version. No dummy identity. |
| HostRecord/selector, per-executable approval, registry/profile/case permission | `/4` admission retains checkpoint B, production/test invocation and eligibility only. No profile or registry exists on the job. Hardware data hash remains an existing model restriction, never a human token. |
| Source/archive/cache/log/review reads, root placement and executable hashes | User selects an installed executable. No source or evidence reads in launch/replay. |
| Custom trusted startup and A-F3 | Normal user-controlled Python installation. Startup substitution/defense-revert experiment not run. A-F3 retired by user scope change, not fixed/passed. |
| Runtime imports from validation/review/test trees | Seven independent checker modules and ordinary schemas included in the wheel. Historical host/review/construction/image modules excluded from the wheel. |
| Old startup assurance tests | `test_component_trusted_start.py`, `test_component_startup_inventory.py` and current-source identity gates retired. New ordinary-carrier/process tests cover versioning, capability invocation, input/output refusals and replay. |

Historical `/3` DTOs, schema bytes, native internal semantic tests, sealed K2 artifacts and
oracle expectations are preserved. Shared semantic validators now accept the explicitly
versioned ordinary types as well. Old development consumers/tools and their record-format
checks remain only to interpret or reconstruct historical evidence; none are required by
the new build or runtime. Their passing tests do not qualify the successor or resolve
B-PROV-STAGING-01. The affected historical observations `/2` restriction and old trace/container incident facts
remain unchanged. The optional legacy `trace_hash: null` result slot does not enable tracing
or require a tracing artifact.

## Runtime dependencies and observed installation

Linux x86_64; Python 3.12+; the non-editable installed wheel; locked declared runtime libraries
(Pydantic, NumPy, PyYAML, Typer, Jinja2 and their transitive dependencies); a selected native
binary; normal system loader, `libc.so.6`, `libgcc_s.so.1`, `/proc` and writable temporary
storage; and the input files. Replay needs the Python installation and saved job/result only.
There is no dependency on `.git`, developer source, Cargo cache, reviews, docs, compiler logs,
root-owned selectors or test directories. Exact installed versions and imported module paths
are in [the runtime observation](evidence/installed-run.stdout).

Builds used the existing accepted Rust 1.99.0 image
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`, unchanged Cargo.lock,
and the existing offline cache. No tool or dependency was added. An initial offline index
resolution attempt lacked cached metadata; locked offline non-editable `uv sync` worked,
then the final built wheel was explicitly installed with `uv pip install --offline --no-deps
--reinstall`. No editable install was used for runtime independence.

The runtime containers used the already-local `python:3.11-slim` image with a copied existing
Python 3.12.14 runtime and its installed virtual environment. The container image ID and
exact mounts are recorded in `evidence/installed-*-container.json`. Only runtime files,
inputs, output storage and (execution container only) the debug/release binaries were
mounted. No source/evidence/cache/docs checkout or Docker socket was mounted. Replay used
a separate container without a native-binary mount. Test-only import guards disabled
preparation/mapping/development modules. Python `open` observations and module paths are
recorded; this is a dependency smoke test, not exhaustive syscall tracing or hostile-startup
assurance. Runtime code has no audit-hook or custom startup requirement.

## Executed verification and retained obligations

- Ordinary production-hardware positive: **656000 ps**; explicit fixture positive: **121000 ps**.
  Debug/release output bytes match for both. Both pass installed API and saved replay;
  production also passes installed CLI run/replay.
- **22 installed negative controls** reject incorrect native jobs, wrong model/job/result
  bindings, observation versions, changed independent timing laws, and nonzero statuses.
  A separate binary-free replay process passed both cases. Case-specific literal expectations
  remain development regression data, not a finite-case runtime admission inventory.
- Native semantic regression: **90 passed, 5 ignored**. Ignored tests require explicit older
  private campaign inputs; they were not executed or called passes. Debug/release builds and
  all-target Clippy pass using the pinned tools. Model/2 issue-edge, lifetime/capacity,
  resource, clock, ownership, work and ordering tests remain in this regression.
- Final ordinary binary plus shared process/framing/deadline/cleanup tests: **23 passed**.
- Ruff, both mypy commands, import boundaries, historical/ordinary schema freshness,
  native `/4` export freshness and canonical prompt synchronization pass. The seven packaged
  independent checkers preserve the old implementation ASTs apart from import paths.
- Final affected Python/native/contract/validation regression: **1470 passed, 3 skipped**
  ([log](evidence/python-final-affected.log)). The skips are the two missing human L1
  worksheets and the historical B native-selection campaign, not ordinary launch gates.
- Git/import-environment dependent U2 and analytic-report recheck: **153 passed**
  ([log](evidence/python-environment-recheck.log)). These development tests ran in a fresh
  disposable Git checkout with a local development install and no PYTHONPATH. This is
  distinct from the non-editable, Git-free installed-runtime evidence above.
- Initial broad regression: **2721 passed, 25 failed, 21 setup errors, 36 skipped,
  286 deselected; exit 1**. It is not reported as a passing run. The complete failure
  scope is recorded in `evidence/initial-broad-failure-scope.json`: nine retired current
  ADR/source-pin assertions; two U2 policy checks subsequently covered by the successful
  environment recheck; 34 analytic-report cases requiring developer Git metadata, also
  covered by that recheck; and one metadata-import guard covered by the successful final
  affected suite. Unchanged passing broad scopes, including analytic/golden/determinism
  tests, were not needlessly rerun. Earlier failed native/schema/packaging checks are
  retained as development diagnostics; final builds, static checks and installations pass.

The source-free installed smoke and native tests were executed here; no prior runtime
approval is used as their evidence. Retained historical evidence is limited to unchanged
human L1 records, historical sealed K2/oracle data, earlier reference observations and the
accepted dependency/toolchain baseline. Those campaigns were not repeated. Current repository checks explicitly report
`H-L1-DMA-01` and `H-L1-GEMM-01` human workings absent; those are skips and the
applicable L1 acceptance remains blocked, not passing inherited evidence. Cargo manifests,
lockfile, model mathematics and golden expectations were not changed. Human L1, U0024,
U4b/reference readiness, G3a and later full-table/performance/silicon obligations remain.
No remote CI was polled. Cleanup only named full container IDs returned by this task's
`docker create`; no label sweep, prune, root/server alteration or image distribution ran.

The final integrated run began on the settled behavioral source; one trailing blank line
was normalized in the extracted transport while it ran. No executable Python statement
changed. A trailing blank line in Hatch configuration was also normalized; its parsed
configuration and wheel contents were unchanged. The initial broad run exposed obsolete whole-ADR/source approval assertions; these
were removed rather than given a replacement approval manifest. Historical ADR-prefix and
archived case-data integrity checks remain. The first affected run then exposed two historical `pyproject.toml` support pins and the
blanket importlib guard. The metadata/oracle pins were preserved by restoring pyproject
and using standard Hatch configuration. A narrow protected allowance admits only
`from importlib.metadata import version`; dynamic imports and vendor access remain refused.
The final affected integrated regression was restarted only after those compatibility fixes
settled; earlier nonzero runs remain separately recorded, never relabelled successful. The exact final wheel was reinstalled and the installed smoke repeated afterward.
Native sources and semantic validators were unchanged throughout that final run.

## Outstanding work

Focused independent review and human installation of the complete protected transition
remain. `H-L1-DMA-01` and `H-L1-GEMM-01` human workings remain absent in the repository;
applicable L1 acceptance remains blocked. No U4/G3a closure or shipping claim follows. A-F3 is retired, not repaired;
B-PROV-STAGING-01 remains unresolved historically in the removed architecture. The known
affected historical observations `/2` behavior remains restricted. No unresolved implementation defect was observed in the executed final scopes. The initial
nonzero broad run is retained honestly with its exact retirement/recheck accounting above;
there is no claim of a fresh all-repository or hosted-CI pass.
