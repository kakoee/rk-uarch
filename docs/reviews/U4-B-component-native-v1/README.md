# B component native verification — preparation complete, candidate join paused

The coordinator confirmed that A is still implementing and has not handed back a
published native candidate. At the user's direction, B finishes this independent
preparation and pauses at that dependency. There is **no native candidate audit,
engine build, native test execution or fault-restoration result in this package yet**.
Resume only from A's exact published source freeze and handoff. Do not inspect or poll
A's changing clone. This is author verification preparation, not independent acceptance.

## Published inputs and ownership

B used its existing rk-uarch-u4-b main clone, integrated published main and preserved
peer/optimizer history. Initial preparation is published at 9b5e3fc (including earlier
80b7aa5 and 7458ca5). Changes are new B validation helpers/tests and this review package.
No installed contract, native implementation, engine runner, optimizer file, K2 root,
authority or historical fixture/selection/expectation was edited.

[Preparation audit](preparation-audit.json) checks the actual approved-document hashes
and all 29 installed postimages against human commit
3949b104d0eaae95a7452f976c2afa048fa82ff1. All 56 current selected-support files equal
their human-installation bytes. This B delta therefore needs no U0002 generation;
that finding grants no protected-source installation permission. The combined A/B
source/import/support delta still requires inspection after A publishes.

[Current input freeze](input-freeze-v2.json) has selection hash
`sha256:2773e630e053a1940672f01ac0a89c1334c8c98d6ceca1b02ef70664df0f4a35`.
It contains 111 prospective definitions: 106 historical cases, genuine O2, and four
additional capacity negatives. All 106 historical graph/point placements and expected
values remain exact, including A/B distinctions and old C04's arithmetic-only 1855000 ps
with its original early refusal. Each new /2 profile binds the exact policy tuple.
Derived profiles, registries, selections and synthetic Trust files are proposals only.

The original [first freeze](input-freeze.json), selection
`sha256:c5c4db8858324d9d4deacf7077f2d4237a2186a71cb4b6d622ad1246f3a45b83`,
is preserved. Version 2 changes only the source hash for a local Python type annotation
and the enclosing selection hash. Every input/profile/expectation/archive member is
identical. The archive SHA256 remains
`32d365dd793f70cbf11033f53f7466bf7c55ca558df2d0ee0bbc1c16ab29f488`.
This is an explicit prospective binding transition, not a rewrite of review history.

Reconstruct into a new private directory with the pinned existing Python environment:

```sh
PYTHONPATH=contract:src:. python docs/reviews/U4-B-component-native-v1/freeze_inputs.py /tmp/new-b-component-inputs
```

Compare its `input-freeze.json` with the published `input-freeze-v2.json` and its archive
hash above. Two private reconstructions were compared byte for byte. The generated
archive is deliberately not committed: automatic approval review rejected publication
under the artifact-generation restriction. The source recipe, complete member hashes
and profiles' identities are published; no artifact adoption is claimed.

## Executed evidence and layer distinctions

The [seven-stage final affected check](checks.json) passed: **21 tests**, Ruff lint and
format checks, strict mypy on the three new typed helpers, identity/support audit,
patch whitespace and exact reconstructed-input comparison. The 21 tests are seven
new input-preparation checks, twelve new attack-constructor checks and two historical
selection/identity joins. No tests skipped. This is a focused preparation check,
not a whole-suite or native result. The private Rust harness also passed rustfmt in
the accepted image; it has not been compiled against A's candidate.

The twelve attack-constructor tests use explicitly synthetic accepted unit anchors.
They preserve work, traffic and makespan and distinguish these outcomes:

| Synthetic attack | Real structural result validator | Independent /2 checker |
| --- | --- | --- |
| Clock-consistent response 58500 ps instead of 59000 ps | Admits | `mechanism duration` |
| O2 allocation 0, late free 2735000, or persistent free | Admits | `accumulator lifetime mechanism` |
| O2 free at first final consumer 1641000 | Admits | `allocation access lifetime` |
| O2 omit eligible dependency cause while resource cause remains | Admits | `complete eligible causes` |
| Missing NoC occupancy / false DRAM latency occupancy | Refuses | `required occupancy` |
| Incorrect channel/DMA null clock | Refuses | `nonclocked exact binding` |
| Incorrect ordinary queue clock | Refuses | `ordinary queue exact binding` |
| Channel population changed to inflight | Refuses | `channel population lifecycle` |

No guard was removed in this preparation run. Historical accepted F5/O2 discrimination
and restoration evidence is inherited, not rerun or counted here. `check_forgeries.py`
will exercise actual saved native output and remove one guard at a time in a private
checker copy. It checks literal failure reasons, positive controls, imported source
origins and exact restoration. It reports generic-checker versus complete-consumer
results separately: O2's extra literal endpoint assertion is an additional defense,
so generic lifetime-guard removal must not be described as bypassing that full consumer.
The early-free access/lifetime overlap remains an alternative-refusal obligation.

The four historical capacity cases still refuse at the profile layer. Four distinct
new private positive-profile cases reach the Python resource guards with the original
bad graphs. Some lifetime/resource JSON also fails MappedEngineJob construction.
The private Rust harness therefore consumes raw JSON and a separate synthetic Trust
file. **Rust reach and its refusal code are still untested**, not inferred from Python.
The public D3 mechanism remains a separate reviewed/approved implementation dependency.

Development corrections were preparation-code corrections: use the existing
`canonical_json` API; recognize that `admit` includes resource preflight; type the raw
private-job dictionary for strict mypy. No engine expectation was retuned. Initial
assertion/static failures were fixed; only the final executed outcomes above are passes.

## Native work queued for the exact A freeze

The [private plan](private-run-plan.json) selects 46 cases, both modes and three fresh
processes per case/mode: 276 planned calls. It covers resident/cold compute, unequal
clocks, rational channel carry, credits, FIFO/ports, overlap, barriers/zero-hop, @1,
transient @2 and distinct profile/resource negatives. The private probe is cfg(test)
only; it is added to an isolated committed export and is not a production bypass.

`build_private.py` requires an explicit full commit already on origin/main, copies the
accepted 1,719-file cache, verifies its recorded hashes and diagnostic bytes, and uses
the previously approved bounded read-trace monitor. It records source pre/postimages
for the added harness and actual test-executable hashes. `run_private.py` checks exact
input/checker/binary bindings, runs fresh network-disabled containers with no producer
source mounted, and compares complete debug/release bytes. The helper interfaces and
Rust harness have not yet been exercised together; missing evidence remains pending.

Resume in this order after normal main integration:

1. Verify A's published source/build handoff, actual public-binary/runtime identities,
   installed-source deltas and the unchanged independent input bindings. Agree any
   interface corrections in a new explicit prospective binding; preserve this package.
2. Build private debug/release unit executables. Run a focused development batch on C02,
   D01 and O2, reconcile concrete failures with A, then the single final 46-case plan.
3. Validate actual /2 output and all independent literals. O2 must allocate bacc at
   producer b start 547000 and free only at complete final-consumer endpoint 2188000;
   duration 2735000, useful 1050, issued 1966080, SRAM 500/210 B and no HBM traffic remain fixed.
4. Execute the saved-output forgery/guard-removal/restoration recipe, establish native
   implementation fault targets on exact source preimages, and distinguish wrong
   results/unsafe acceptance from identity or alternate refusals. Do not repeat F6 or
   broad unchanged sweeps. Native fault target postimages cannot be frozen before A's
   actual source is available; none is represented as accepted here.
5. Apply the preserved read-audit inventory parser to new traces, inspect runtime and
   import/source origins, and record limitations. Traces are bounded observed reads,
   not universal closure or hosted qualification. Verify source/cache restoration.
6. Complete actual binary/replay/runner identities and one affected integrated handoff.
   The current package supplies plans and tests, not those missing results.

## Later public use and remaining human boundaries

[Public-first-use proposal](public-first-use-proposal.md) describes the deterministic
111-case/666-call proposal, exact profile/registry/selection joins, budgets and immutable
placement/preflight needs. Its public-job engine/build fields must be constructed from
real accepted runtime identities in a later selection. Synthetic job anchors and private
unit executable hashes cannot replace real HostRecord/selector/BuildTrust authority.

No new release/pin/licence vote is needed for approved private implementation. Still
pending: A's frozen candidate; the next independent review; actual component runtime
and first-use authority/placement; separately reviewed D3 negative transport; genuine
human L1 GEMM/DMA workings at L1 acceptance; U0024 remote qualification. The 70-row TPU
proposal remains unchanged, unmeasured and separate, with no placeholder reference or
reference-access prerequisite for bounded implementation. No public mapped jobs,
artifact adoption, positive badge, adversarial acceptance, G3a or U4 closure follows.
