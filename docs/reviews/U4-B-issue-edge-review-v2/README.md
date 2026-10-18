# B bounded recheck of B-ISSUE-ORDER-01

**Disposition:** B-ISSUE-ORDER-01 is resolved in A's exact revised, unapplied proposal
`7d61d6a02644519d4a7b8b1ce9287e60cd03ca13`. No remaining implementation finding was found
in this bounded recheck. This is author verification and peer reconciliation; it is not
independent adversarial acceptance, protected installation permission or execution authority.

B read the manifest and peer-reply, integrated published main normally, and reconstructed
both routes in separate private exports. Both have all **22 exact postimages** and the
complete exports are identical across 5377 files. Ordered apply/reverse checks and all
nine historical byte controls passed. [reconstruction.json](reconstruction.json) pins every
pre/postimage and both routes:

| Route component | SHA256 |
| --- | --- |
| Full contract-and-export.patch | `c0053243d3e96cd25496823ad980742c25b9721850f87f55628b640876fe1b75` |
| Full checker-and-identity.patch | `ef93116d948f40ab869a080c516bba4576c8803cafa46a4a161bbff5051c29a7` |
| Full native.patch | `32c2c0452f86cbdf6ce89cee3eb1ba1f1df1f33853ec4391384cd54574ea8ebc` |
| Alternative delta after exact assembled v1 | `6541eb4ef01eecccbb887a129e2d8f035d9693233f22b8f0c3aa11a6dbc5d5fa` |

The full route starts at `d4ef3bf00f53c693a9a8188e5edc368862e187f3`. The alternative starts
from the same export, assembles the three original v1 patches, verifies their exact
postimages, then applies only the alternative delta. The two routes are not cumulative.
[source-delta.json](source-delta.json) records 14 changed/added postimages relative to v1.

**Actual transition and checker assessment.** Native starts with eligibility dirty,
records the endpoint cursor before reservations, and appends actual grants as they occur.
A terminal sequence sets eligibility dirty. Scheduled phase-0 completions drain together
before the next reservation pass; each inline terminal reaches the next pass separately.
Nonterminal completions and pending conversion do not create an opportunity. Repeated
passes without a terminal transition do not invent opportunities. The final terminal
still yields the explicit empty opportunity. Accounting projects this stored state;
it does not substitute the later issue-alignment ordinal.

The checker reconstructs opportunity boundaries from job and request terminal endpoint
ordinals. The union covers every DMA fragment terminal and the single compute, unicast
and barrier sequences. A dependency job's maximum terminal ordinal requires all its
sequences to have completed before the cursor. Previous grants retain capacity until
their request terminal is strictly before that cursor, covering pending and acquired
states once. The checker derives the eligible population and available per-engine slots,
then the complete earliest grant list ordered by readiness, engine and request. It
compares the claimed list against that result. It does not trust claimed opportunity
order or equal readiness timestamps as proof of eligibility.

B independently derived the opportunity boundaries from the **prior B endpoint receipts**
and mechanism terminal names, without the new checker or native implementation. Both
revised modes match `[cursor,time] = [(0,0),(2,0),(17,26667),(28,60000),(50,120000)]`.
See [independent-boundaries.json](independent-boundaries.json). In particular, initial
reservation is at cursor 0; issue alignment is later. The inline unicast completion
produces cursor 2, and the barrier and DMA terminals produce the remaining opportunities.

**Reproduced cases and forgery.** The original raw input hashes remain exactly
`70494e8cf7476e8906bd148606ff3613f25e5864fc3789c9e13dcdabad2aa38b` (r00 dependent) and
`3263938d73234a257434327840e986336f48b37b99159904b6a78b6f8bfd7636` (paired r01 dependent).
Both inputs reach real Rust admission/execution with synthetic private unit Trust.

| Case | Initial grant | Grant at 60000 ps | Structural / independent |
| --- | --- | --- | --- |
| Original failing r00-dependent graph | r01.00 at cursor 0 | r00.00 at cursor 28 | pass / pass |
| Paired r01-dependent graph | r00.00 at cursor 0 | r01.00 at cursor 28 | pass / pass |

The first request reserves/issues at 0 and completes at 60000 ps; the second reserves/
issues at 60000 and completes at 120000 ps. Opportunities at cursors 2, 17 and 50 grant
nothing. All four new debug/release results pass both consumers and match A's published
outputs. Each mode agrees byte-for-byte with its pair. Removing **only** the new witness
and recomputing the result hash restores the complete prior B result exactly; no timing,
traffic, count, queue, cause or allocation expectation was retuned.

B constructed the early-eligibility forgery from its freshly executed paired output,
rebound it to the original graph, repaired the dependency causes and resealed identity.
Its bytes equal A's published forgery, SHA256
`fb737fff66fd88c65ccb12991252b30c6176247902a2c17e75f5edb0b7c946b4`.
Structural validation accepts it. The independent checker rejects it specifically at
`opportunity eligible grants / ready tie`: r00 is not yet eligible at cursor 0.

[eligibility-fault.json](eligibility-fault.json) removes only the dependency-completion
predicate in the private checker. That admits the complete forgery while the paired
valid control stays accepted. Exact restoration rejects the forgery and accepts both
real cases again. This is unsafe checker acceptance, not an incidental hash/schema
refusal. Under the fault, the original r00-dependent valid result is falsely refused,
as expected when timestamp-only ordering reappears. The initial fault harness wrongly
required that result to remain accepted; its assertion failed and the `finally` block
restored exact bytes. The corrected control expectation and fresh fault/restoration run
are recorded; this setup mistake is not a candidate defect or discarded model failure.

Four additional joined output attacks omit the empty inline opportunity, omit the final
release, invent a nonterminal opportunity, or delay an initially available grant. All
four pass structural validation and fail independent inventory/earliest-grant checks.
[consumer-checks.json](consumer-checks.json) records the five attacks separately from
valid native outputs. Earlier draft /3 outputs remain historical evidence; missing the
new required witness does not silently become acceptable under the revised proposal.

**Preserved behavior and focused evidence.** B executed 12 additional synthetic helper
controls: eight positive literals and four intended refusals. These cover cap1/cap2,
independent pools, same-opportunity tie reversal, unavailable reserved capacity, all
predecessor terminals despite an already free credit, phase-0 coalescing versus inline
epochs, and strict-wait readiness 59999/60000/60001 ps. They are helper fixtures, not
mapped/native outputs. The strict-wait function is unchanged from v1. Pending conversion,
capacity, explicit zero alignment and reservation-based job/allocation starts retain the
previous law; no new timing mechanism or issue-rate cap was introduced.

Fresh isolated debug/release targets compiled the exact revised source plus the unchanged
B cfg(test) probe. All 1719 accepted cache files, lock/features, source postimages and
executed binary hashes were verified. [build-bindings.json](build-bindings.json) records
commands, image/tools, native source inventories and bounded monitor receipts. No stale
Cargo executable or previous build target was reused. Unit executable SHA256:

- debug: `f9d250f589ddfd517786cfc150d088ddaed454c8f61a6e01a6768d36f4a872f1`
- release: `f32918c920f09b2fc613942253d35cb373a8bb27961168dcdf3cc60f12317432`

New native execution is limited to **four explicit mapped probe processes** plus the
**12 focused proposal controls in each mode**. Those controls include the paired raw
regressions, synthetic terminal-batch test, preserved strict-wait/capacity/33-issue tests,
version boundaries and the three historical full-output byte controls. Typed-state tests
are not counted as mapped admission. A's separate native fault sweeps are inherited,
not claimed as B executions.

After exact restoration, one affected Python/static batch passed **43 tests**, six-file
Ruff checks, four-file strict mypy, schema generation and all three snapshot modes.
[python-checks.json](python-checks.json) and [native-runs.json](native-runs.json) bind the
executed commands. [checks.json](checks.json) records the bounded disposition and counts.
Exact executed recipes are retained where later import-order/string-wrap cleanup occurred.

**Prospective identity and remaining boundaries.** The revised overlay retains six exact
replacements and six additions and is externally pinned by the manifest. The historical
installation binding and 106-case selection are unchanged; the new checker, schema and
ADR postimages are prospective. All 56 selected U0002 support files are unchanged, hash
`sha256:676b12509606b7a519d9597dc406f8fe66d141af4c86425a5baf3a2e3825358a`.
No new human U0002 generation is triggered by this correction. It does not authorize
installation. Old model-1 paths, K2 history and runtime authority remain separate.

This is B's concrete reply to A's peer-reply: the actual-eligibility choice, transition
witness, checker discrimination and exact revised identity joins resolve B-ISSUE-ORDER-01.
Human approval of the semantic/version amendment and protected installation, genuine L1
workings, later runtime/placement/profile/registry/selector/HostRecord bindings and public
negative transport remain pending. No authority or protected live source was changed.

The earlier twelve-case campaign and unrelated mechanism evidence are reused, not rerun
or relabeled as revised-source execution. No trace rebuild/capture occurred. Unknown
`debug.trace.450:11` and `debug.trace.452:9`, and unfinished
`release.trace.482:10` sched_getaffinity remain the same unaccepted read-audit gaps.
No public component execution, independent-review verdict, qualification, G3a or U4
closure follows. R/TPU readiness remains separate.

Reproduction: run `reconstruct.py /tmp/FRESH`; build the `full` export with
`build_private.py SOURCE /tmp/FRESH-BUILD`; run `run_final.py BUILD /tmp/FRESH-RUNS`;
then use `consume.py SOURCE RUNS OUT` and `eligibility_fault.py SOURCE RUNS CONTROLS OUT`.
Use the pinned existing Python environment and explicit
`PYTHONPATH=SOURCE/contract:SOURCE/src:SOURCE`. The independent boundary comparison uses
hash-bound prior B receipts. Raw paths and hashes are in [private-receipts.json](private-receipts.json).
