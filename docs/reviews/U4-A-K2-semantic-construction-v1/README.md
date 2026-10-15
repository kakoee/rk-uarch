# U4 A — bounded semantic and construction addendum

Proposal complete for coordinator reconciliation; **no K2 implementation or execution
release**. The published loader is retained without correction. Only this new package is
added. Earlier A821dc90, B8b7a647, B5422511 and coordinator packages retain their bytes.

Main was integrated normally through4ede30dfdfc59d64ea4567d6d5597359cdb2d5d3. Required
inputs were the [coordinator request](../U4-loader-K2-reconciliation-v1/README.md),
[B's original peer review](../U4-B-K2-first-use-v1/peer-reconciliation.md), acceptance and
coverage, and [A's retained proposal](../U4-A-loader-K2-preparation-v1/README.md).
The subsequently published [B supplement](../U4-B-K2-semantic-reconciliation-v1/README.md)
and [coordinator check](../U4-loader-K2-reconciliation-v1/B-supplement-review.md) are joined
explicitly in [peer-join.md](peer-join.md). B has not reviewed these new A bytes.

## Concrete deliverables

- [Semantics and exact case mapping](semantics.md): raw next_edge(1.2GHz,835,0)=1667
  independently observed; owned zero grant835 completes835. Earliest release, dependency/
  owner delays, positive/zero cycles and same-time phase/FIFO rules are concrete. No hidden
  Python job or runtime-duration preprocessing. Raw/K07 counts stay explicit; the exact
  remaining arbitrary Wheel private/public exception is proposed, never silently granted.
- [Complete unapplied patch](complete.proposed.patch), [pre/post hashes](patch-manifest.json):
  ten paths, including mapped carriers/checks, three changed generated mirrors, three
  affected test files, U0011 and synchronized U-P11a/build-spec. It covers all three event
  additions, real raw-clock observations, release_ps, nullable non-clocked FIFO domains,
  typed release idle, causal ties and empty all-zero-duration partition. Critical records
  are positive only; zero bridges remain in job links. Idle never adds busy time.
- [Construction plan](construction.md) and [exact machine constraints](construction-plan.json):
  direct pins/features, retained/new transitive allowlist/checksums/sources, required actual
  resolution/licence/cache receipts, canonicalization matrix and software-path/no-SIMD
  evidence. These remain candidates, **not a resolved closure**. C1 resolution/fetch only,
  C2 offline standalone probes and C3 image distribution are separate permissions.
- [Acyclic record and read proposal](identity-and-reads.md), [six schema models](record_models.py)
  and their generated [schemas](record-schemas/BuildInputs.json): profiles/trust before
  source/tool identity, generated outputs excluded from their own inputs, separately verified
  debug/release binaries, then human decision and external host selector. No final receipt
  hashes itself. Build-test trust cannot confer qualifying first-use authority.
- [Read inventory](read-inventory.json), [validation receipts](validation/checks.json) and
  [preservation receipt](preservation.json) distinguish actually checked current source from
  proposed future build/host reads and from unexecuted native obligations.

## Executed checks and limits

Final private exports of4ede30d: **123 proposed-schema/affected tests pass** and **119 host
checks pass**, zero skips. The123 include76 contract tests,43 loader tests and4 prompt-sync
tests. The119 include17 A arithmetic/metadata/construction controls,55 preserved B
literal/membership/installed-gap controls,43 unchanged loader tests and4 prompt-sync tests.
These selections overlap; they are not242 distinct native cases.

Both CI-form typing commands pass (83 source files,33 contract-test files); repository
Ruff passes. All12 mapped mirrors were generated in scratch; exactly3 change. A third
fresh export reproduces all10 patch postimages and schema freshness. Live patch apply-check
passes without application. The six proposal metadata mirrors reproduce exactly.
Strict baseline currentness and B's loader/support read audit pass:26 loader files,56
selected support files, explicit saved-job-only read and no implicit authority discovery.
Counts are observations, not quotas. Live production/protected/dependency/artifact paths
and historical package trees retain their hashes.

[Discovery notes](validation/discovery.json) retain setup/lint/typing/structural findings
encountered while completing the proposal, including the affected dual-timing admission
test. The final checks use the corrected scripts and complete patch. No failure was
classified as an executed native mutant. Partial synthetic subrecords cannot serialize
as EngineResult; hand calculations and proposed checks are not executed native evidence.

Reproduce with existing accepted Python tools, without installing anything:

~~~sh
/path/to/existing/python -I -B docs/reviews/U4-A-K2-semantic-construction-v1/run_checks.py
~~~

The runner exports current published HEAD into private /tmp directories and constructs/
checks the proposal there; it never installs the patch. For this recorded run, HEAD was
exactly4ede30d. It returns raw logs and exact commands under a new private receipt directory.
The builder refuses a live checkout or a non-/tmp root.

## Decisions and stop

Coordinator must reconcile the explicitly different raw-observation, queue, zero-bridge
and phase choices with B; accept exact semantic/schema/ADR/public-coverage text before any
new finite corpus freeze. The zero-bridge representation and phase1 release are actual
remaining joins, not implicit B approvals. No historical expectation or profile is edited.

The smallest construction permission to consider next is **C1 only**: one allowlisted,
checksum-recorded private Cargo resolution/fetch, with no compile/run, live lock/cache,
image installation or publication. Its exact scope is in construction.md. This follow-up
does not request or exercise it. Actual dependency acceptance, C2 probes, protected/live
installation and final human binary/host first-use authority remain separate decisions.

No native command, new dependency/image construction, oracle generation/adoption,
production change, CI polling, remote setup or performance claim occurred. U0024 and the
original human L1/model boundaries remain. Stop for coordinator reconciliation.
