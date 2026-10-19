# Proposed diagnostic policy and startup obligations

B's complete decision at `docs/reviews/U4-B-capture-diagnostics-v1/decision.md` is the exact proposal. Its final evidence commit is e964215ce1b99fd3941be41d6badd6e133c42dfd, integrated at097a69033668a3fc457fb4b6649370a1d4948b16. Manifest SHA256 is8df9614e5c828ee37c050bda598ec228c2f9e14b05d7369a75a0c564d5ed0ba0. All25 leaves match. The policy bytes remain0b184913e4d13ea7be2f16ff131dafde2322657d649d2dad22d515a8efa2d6e8; human acceptance is pending.

Plan/receipt /2 binds `inputs.capture_diagnostic_policy`; production BuildInputs /3 and recipe /2 bind the unchanged native child argv/environment. The fixed tracee wrapper redirects child stdout/stderr into exclusive fresh per-phase files and then execs positional child arguments. Tracer/bootstrap guardian channels remain separate and must exist and be empty. Legacy plan /1 remains unwrapped and conservative.

| Channel | Canary cap | Debug/release cap | Proposed condition |
| --- | --- | --- | --- |
| Tracer/bootstrap stdout and stderr, each |65,536 bytes|65,536 bytes|Both empty; any diagnostic or mixing refuses.|
| Child stdout |4,096 bytes|16 MiB|Exact canary sentinel or complete classified Cargo JSON, exactly one final successful build-finished.|
| Child stderr |4,096 bytes|4 MiB|Exact prospective canary cat diagnostic, or exact phase-specific reviewed full lines.|

Canary stdout is `U4-read-canary-v1` plus newline. Its missing-file stderr is `/bin/cat: /canary/absent: No such file or directory` plus newline. These are synthetic prospective expectations, not newly measured image output. The unique absent-file cat exits1; sentinel cat/root/other processes/guardian exit0. Build processes and guardian all exit0. Only compiler-artifact and build-script-executed records followed by successful build-finished are allowed; compiler-message and unknown/truncated records refuse. This is output classification, not artifact adoption.

The supplied debug/release stderr lists are empty. Any nonempty real build stderr currently refuses. Synthetic compiler-line fixtures are never incorporated into the proposal. Concrete real line lists require a separate exact hash-bound policy decision; there is no broad warning/Running-prefix whitelist. Loss/truncation/unfinished diagnostics cannot be reclassified as safe lines.

Trace-supported wrapper/child exec, exclusive opens/redirections, complete process tree/terminals and exact successful-write bytes must independently support attribution. Single writer per child stream is required; multiple writers without order proof, writev, undecodable/truncated/unsupported mechanisms, unknown records and missing streams refuse. Caps retain overshoot and refuse; they are not filesystem quotas. Unchanged total budgets are canary30s/16MiB and build600s/512MiB, with200,000 trace records maximum. Retained failure records are not cleaned into success. `read_audit_complete` remains false even for an accepted diagnostic/mock receipt; empty tracer stderr is not an independent loss counter.

The final source binds the actual diagnostic helper/test, construction specification, combined monitor and all existing parser/helper inputs. Exact source, import, consumer and startup project transitions are in source-transition.json and evidence/inventory-transition.json. The startup tool patch only extends project enumeration; no construct/bootstrap/launcher invocation or new startup manifest ran. The saved external inventory is unchanged and byte-verified; existing startup evidence cannot be inherited as proof for added closure.

Later authorized construction must independently bind the concrete policy, exact wrapper command, accepted image/shell/tracer and startup dependencies, startup roots/manifest, tools/cache, limits and generated identities. No new shell/loader/cache hash or deployment root is fabricated here. The external interpreter/bootstrap/loader/cache trusted-computing-base limitations and all three read gaps remain. A-F3 is deferred and its blocked activity was not retried or transferred.

B's actual final confirmation of these combined postimages is pending. Policy acceptance, protected/default-route/D3 installation, activation build, placement, deployment, genuine authority and public first use remain separate; the hashes in this package authorize none of them.
