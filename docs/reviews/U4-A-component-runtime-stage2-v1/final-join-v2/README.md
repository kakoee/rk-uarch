# Consolidated Stage 2 final A/B integration candidate

Runtime source **46c5abb248b5d58304f35628f84e5919e122f989** incorporates B **3c70b714dbe188bfe808a7a0890ffa5b53fcc0a1** through normal main integration. This additive package supersedes the earlier A Stage 2 handoff's *pending build/interface join* disposition. Earlier source, packages, reviewer evidence, inputs and receipts remain unchanged. It is a private engineering candidate, not B acceptance, deployment or execution authority.

The final join implements B's admitted-input record at A's direct saved-result boundary, passes it from B's consumer, freezes caller-owned campaign acceptance before constructing the adapter, and binds the unapplied D3 expectation provenance to the selected input, engine, exact envelope and native guard source. The consumer closure has 61 files: four changed pins from B's frozen record (A host, records, runner; B's one-line `admitted=admitted` bridge). B must review that bridge and this exact closure.

## Actual source/build/runtime freeze

[identities.json](identities.json) contains full identities, changed files and executable paths. New engine implementation: `sha256:336f1ea96c65da3ef24f12101dac78abf388523b7a20b640a5474b2e31188939`. New payload: `sha256:6c0c3700ed4e936f3df32644ad07bb66ffeb33bcd8871bb621214f6c05b54ba2`.

| Actual executable | SHA-256 |
|---|---|
| Ordinary debug | `1f80b84650a5f2b43954b5654a84cba32d570b86766bb9b78adb0d3443444958` |
| Ordinary release | `fad2ae795c85e2086474c7ab39cf9bf865674291cdb4b5a2e603968f2bd0f0c4` |
| Private cfg(test) debug | `979b8440964754e79eea96d39212f7cc2884b4a98f8bdfd0ba4637ceecbdb609` |
| Private cfg(test) release | `0f01e110f07c9f68c3e9204720832dbeed5375c56889f3f09354cff4cc79011b` |

Both ordinary and test executables were actually built once in fresh debug/release targets using the accepted image, tool versions, locked features and 1719-file offline cache. Ordinary binaries have new identities. The newly built test executables equal the previous cc899d2 test bytes; this supports reusing unchanged Rust unit evidence, not production reproducibility. Source/generated/cache postchecks and ordinary ELF/loader/DSO observations passed. No construction read trace was captured. Model source and ToolInputs hashes remain unchanged. BuildInputs has 235 entries: ten existing entries changed, seven were added, and 218 remain unchanged relative to cc899d2. This accounts for the preparation tool and B's expanded checker/harness sources. No Rust behavior, dependency or protected live source changed.

All 124 input definitions were regenerated under the actual new engine. Positive inventory has 104 entries. The 20 negative transitions preserve B's complete prior expectation records and permit only engine/job-hash changes with identical native guard source. Two expectation histories originate at cc899d2, eighteen at c67d558; none is relabelled a new execution. The new private four-case execution evidence is separately bound. Historical selection 124/1368 and the unapproved proposed reduction 120/1344 are untouched.

A post-freeze regression found one test still naming the previous closure path. The one-line [test-only delta](test-path-only-delta.patch) corrects that expected path; its targeted rerun passes. It changes no BuildInputs, consumer or runtime file. The runtime source remains 46c5abb; frozen and corrected test hashes are both retained. No binary was rebuilt for this documentation-path assertion.

## Executed versus inherited evidence

| Check | Observed result and scope |
|---|---|
| New direct consumer boundary | Missing anchors refuse; matching pair accepts; old-engine and consistently rehashed foreign-input pairs refuse. Before implementation, missing-anchor test failed with DID NOT RAISE; the other new-argument failures were TypeError, not evidence of unsafe acceptance. |
| D3 provenance regression | Four rehashed provenance mismatches (raw digest, engine, envelope, guard source) failed with DID NOT RAISE against v4, then passed against v5 with valid paired controls. No protected installation. |
| Development checks | Ten focused A tests, five B bridge/replay/refusal tests, focused Ruff and cold mypy of three maintained modules plus exact D3 v5 passed. An initial acceptance-config test refused the stale pin before additive closure refresh; retained as development evidence. |
| Final-source affected selection | 20 passed; one stale path assertion failed. Its exact one-line correction passed separately. This includes preparation/substitution/consumer checks, matching binding and wrong/stale binding rejection. No startup-substitution test was rerun. |
| Actual new payload | Matching 104-positive preparation accepted. Wrong `runtime_checks.py` pin and stale A runner pin refused at their intended source checks before dispatch. |
| Ordinary binaries | Eight fresh EOF transport refusals: malformed UTF8, unsupported protocol, absent component authority and K2 substitution in each mode. Correct status2; no public success. |
| Direct private native integration | 20 sequential distinct containers: cc0 and transient O2 each with six initial results and one saved-input replay per mode (16 positives); SRAM and C04 profile cases in each mode (four negatives). CPU1/RAM1GiB/PID64/FD256/30s per call, network disabled. |
| Actual outputs and consumers | cc0=121000ps, O2=2735000ps. A structural/direct validation and B's independently frozen literals/check_v3 all accept. Runtime-entry instrumentation is one for positive and zero for negative. SramCapacityExceeded and TestVariantNotAdmitted envelopes match exact B expectations. Both consumers share check_v3; this is not two independent mathematical oracles. |
| Durable replay | Four replays reopen saved inputs; B verifies six initial receipt references and reconsumes their saved input/output bytes before replay. Producer preparation functions are unavailable. All observed per-case bytes match across modes/initial/replay. This establishes persistence/readback and producer independence for these calls. |
| Cleanup | Twenty per-call exact-ID cleanup receipts and parent cleanup report verified stopped/removed with no outstanding containers. Earlier actual timeout/worker-death/cancellation fault/restoration controls are inherited unchanged. |
| Saved-output/D3 join | Twenty new outputs compared with historical c67d558 outputs: positives equal excluding only engine/job_hash/result_hash; negative error bytes equal exactly. Four new negative outputs pass v5 private selected-input/provenance and exact-envelope consumption. No D3 session or authority was constructed. |
| Campaign | **INCOMPLETE**, zero transported/validated calls. Default resource discovery failed at missing `/sys/fs/cgroup/cpu.max`. The failed launch, groups and empty successful cleanup are retained. No resource override, limit assumption, campaign retry or complete campaign verdict. The separately scoped direct per-call controls do not replace this missing campaign evidence. |

The direct-probe driver was first invoked from the wrong working directory and stopped before transport at missing acceptance.json; its log remains labelled setup failure. Its empty directory was removed. The corrected invocation used the frozen export. No missing output was invented.

Earlier A Stage 2 58+1 controls, startup synthetic evidence, exact-envelope/selector/cleanup baseline and fault/restoration results retain their source labels at f86dc5b. B's independent semantic/literal/matrix evidence remains at 3c70b71. The initial direct-anchor/D3 behavioral red logs and restored green logs are included here. Unchanged K2, native law, historical campaigns and broad mutation sweeps were not repeated.

## Finding dispositions and owners

These are author implementation dispositions, not reviewer adjudication. No finding is rejected.

| Finding | Current disposition | Owner/dependency |
|---|---|---|
| A-F1 / B-F7 | Implemented at prepared inventory and direct consumer; matching, missing, old-engine and foreign-input controls executed. | A implementation; B final bridge/closure review pending. |
| A-F2 / B-F9 | B independent literals/closed vocabulary preserved; actual cc0/O2 direct joins pass. Wider semantic evidence inherited. | B original evidence; reviewer adjudication. |
| A-F3 | **DEFERRED.** Defenses implemented and earlier bounded synthetic tests exist; additional real-D11 startup substitution verification remains platform-blocked and was not retried. | Platform/user restriction; trusted startup/TCB activation and later permissible verification. |
| A-F4 / B-F1 | Private exact-envelope controls and actual new negative joins pass. D3 v5 remains unapplied. Source provenance is not universal guard-reach proof. | A proposal; B exact expectations; human D3 installation/authority. |
| A-F5 | No activation/read-completeness claim. Exact earlier U0011 proposal remains unapplied. | Public adapter/environment/read capture decision before activation freeze. |
| A-F6 | Selector version and nonauthorizing acceptance_commit meaning unchanged from implemented f86 correction; earlier tests inherited. | A code; protected policy proposal/human decision remains separate. |
| B-F2 | Actual container guardian and verified cleanup integrated; all twenty new direct calls removed. Prior worker-death/cancel faults inherited. | A; B review of actual receipt join pending. |
| B-F3 | Independent matrix-order checker unchanged. | B frozen semantic evidence inherited. |
| B-F4 | Structured witness plus independent direct consumption executed on actual new private outputs. | A/B; one-line bridge review pending. |
| B-F5 | Failed resource campaign retained as incomplete; direct attempts preserved before validation. No absent output invented. | B harness; resource-discovery environment issue pending. |
| B-F6 | Durable six-reference replay executed four times against actual new outputs with producer preparation unavailable. | A/B final saved-artifact review. |
| B-F8 | Historical campaign preserved; reduced schedule remains unapproved and unused. | Separate human gate decision. |
| B-F10 | All twenty source-labelled expectation transitions preserve prior records; four new actual negative observations separately retained. | B provenance review; no historical verdict widening. |
| B-F11 | New construction read capture **NONE**, cc899d2 **NONE**; candidate-03's three undecodable records still unresolved. | Activation/read-audit dependency, not fixed by hashes or loader observations. |

## Proposals, reconstruction and remaining decisions

[D3-manifest.json](D3-manifest.json) binds the full v5 patch and exact v4→v5 delta; both routes reconstruct the same postimage. Inventory/2 schema is unchanged and linked by hash. Version /2 selector/record/decision/review are required; there is no /1 fallback or K2 authority reuse. The existing unapplied U0011/activation proposal remains at `../proposals/`. No live D3 module or protected installation was made. The native /3 laws and historical /2 restriction are unchanged: same-engine/same-instant acquired-release cases, including write/write and unclassified directions, remain blocked under the accepted prospective first-use policy; there is no /2 repair or waiver.

`source-delta-from-B.patch` reconstructs the complete changed runtime/test source at 46c5abb from B3c70b71. `BuildInputs-delta-from-cc899d2.patch` reconstructs changed BuildInputs source bytes from the published cc899d2 source. The source commit also contains the new 61-file consumer record and D3 v5 text; these are standalone additive files, not part of the source-only delta. `test-path-only-delta.patch` is explicitly a later test overlay. Bindings flow source commit → BuildInputs/generated identity → actual binaries/receipts → payload → caller-frozen acceptance → observed receipts → handoff manifest. No current hash authorizes itself.

The evidence archive includes exact owned source snapshots, build inputs/commands/logs/generated identity, jobs/profiles/registries/payload, acceptance, attempts, blobs, six-receipt replay descriptors, transport/cleanup witnesses, proposal reconstruction and test logs. Actual binaries and the whole Git archive remain in the recorded private root under original identities; their hashes and reconstruction route are supplied, not a claim of independently reproduced binaries. Original reviewer bytes and earlier evidence archives are not repackaged or edited.

A-F3's exact stopped activity and limitations remain in [the preserved platform record](../platform-and-publication.md). The additional real-consumer reproduction never reached a consumer verdict. No retry through another tool/session/path occurred. Existing reviewer evidence is inherited, not a new run. Full immutable interpreter/bootstrap/dependency/DSO activation remains separate.

The [finite B review batch](peer-final-review.md) is ready. There is no connected B session route and no actual B acceptance of these final postimages. B must review the exact bridge, identities, new per-call evidence and the resource-discovery gap. Public adapter/transport/resource environment, construction read capture, deployment/root placement, genuine HostRecord/selector/profile authority, D3 installation, human L1, and public first-use acceptance remain separate. Candidate-03 gaps remain debug.trace.450:11, debug.trace.452:9 and release.trace.482:10; no new trace or reconstruction closes them. U0024 and deferred U-P11b phase-B public L0/L0m/L1, six-way determinism, latency/attribution/critical-path and saved-input replay acceptance remain in force. No R/TPU, qualification, artifact adoption, badge promotion or U4/G3a closure.

Publication is separately pending after the earlier automatic approval rejection recorded in the platform note. This package is committed locally with normal hooks; no alternate push route is used. Source/evidence approval for older named commits is not silently extended to these new private outputs.
