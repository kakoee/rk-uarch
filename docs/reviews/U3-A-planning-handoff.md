# U3 Lane A bounded planning handoff

2026-10-10. **Planning complete; U-P5 has not started.** Javid (@jjaffari) is the acting
human decision-maker for both lanes. No Reza approval, independent review acceptance,
U0005 acceptance, candidate pass, U3 closure or new tag is claimed.

## Exact handoff

Proposal/expectation commit: **`f581b50da69ff9b75b0c6c7a68342da647270200`**.
Review it with `git show f581b50da69ff9b75b0c6c7a68342da647270200`:

- [G2/U0005 proposal](U3-U0005-proposal.md): 200 s proposed point limit derived from a
  24 h / 336-point table-family budget; 14 mandatory BF16 cold diagnostic points, three
  repetitions; candidate/dependency pins, licence gaps, runtime/resources, failure rules,
  fidelity caveats, actual U2 interfaces and updated effort/wait estimates.
- [Independent physical expectations](U3-G2-physical-expectations.md): exact per-operator,
  per-rank and complete-model integer counts, synthetic one-layer scope, unchanged original
  32-layer expectations and discriminators for missing work, repeats, padding, replicated KV,
  paging, embedding asymmetry and replay. These are specifications, not generated evidence.

This handoff is a subsequent documentation-only commit; its exact identity is available with
`git log -1 --format=%H -- docs/reviews/U3-A-planning-handoff.md` and in the session's final
publication message. No self-referential manifest or copied checkpoint tree is needed.

Worked in `/home/jjaff/AI-infra-simulation/rk-uarch-u3-a`, an independent clone with its own
`.git` and local main; origin is `https://github.com/kakoee/rk-uarch.git`. Initial main was
`79bc1f014306e520aacba3491d60ae6c644b26a8`, also the verified peel of annotated `u02-end`.
Fetch before editing and after the proposal commit found no new remote commits; integration
reported already up to date. Normal commit hooks ran, with no UARCH_HUMAN or hook bypass.
Publication uses a final fetch/integration followed by a separate ordinary main-only push;
if a peer wins that race, retain their history and integrate/test/retry without force-pushing.

No shared implementation or B-owned file was edited. The three planning paths were absent
when inspected. Proposed A/B interface ownership is for coordination via Javid, not a claim
of peer agreement. Both full papers and required U-P5/repository context were read; source
checkouts under `/tmp/u3-a-planning` were inspected only. Pins and upstream links in the
proposal suffice to recover them. No simulator/image build, candidate execution/measurement,
adapter, runtime schema, protected file or host configuration was created/modified.

## Checks actually executed

Used the clone's locked Python environment (`uv sync --locked --extra dev`, Python 3.12.14),
installing only existing repository dev dependencies. No lockfile or dependency declaration
changed. Checks returned exit 0:

| Command/check | Result |
| --- | --- |
| `uv run ruff check .` | Passed |
| `uv run mypy src contract/uarch_contract scripts` | Passed, 68 source files |
| `uv run mypy --no-explicit-package-bases contract/tests` | Passed, 28 source files |
| `uv run lint-imports` | Both import contracts kept |
| `uv run pytest -q tests/unit/test_prompt_sync.py tests/unit/test_third_party.py` | 6 passed, no skips |
| `uv run python scripts/vendor_rk.py --check` | Snapshot manifest, matrix and strict current compatibility verified |
| Integer-only document check | All 12 numeric expectation rows recomputed and equal; no engine/producer imports |
| Local Markdown links and `git diff --check` | Passed |

No full pytest suite or analytic demo rerun: only new prose changed, so another 1,394-test
U2 run would not validate new runtime behavior. Existing public analytic/table/report code
is unchanged; retained U2 validation remains at its original identities. These checks do not
constitute fresh public workflow execution or independent review. Native, golden, determinism,
patch application, image licence scan and performance suites were **not run**; no corresponding
implementation/artifact was created. The two third-party register tests pass against the
existing empty register and do **not** certify either candidate image. No nightly run or
runner readiness is claimed; a green empty-suite nightly must disclose its no-op scope.

## Unresolved decisions and next dependency

1. Javid accepts/revises exact proposal commit `f581b50da69ff9b75b0c6c7a68342da647270200`,
   including its synthetic one-layer model, BF16/cold scope, 200 s limit and resource allocation;
   a human commits U0005 pre-registration. This planning publication is not that acceptance.
2. Administrator provisions approved rootless runtime/helpers on native Debian12
   `javid@152.53.209.203`. Supplied subordinate-ID ranges alone do not provide Podman or
   UID/GID helpers. Reza is unavailable; no administrator wait estimate or alternate host
   waiver exists. B verifies the online `uarch` runner, restores nightly schedule and records
   the required green manual run, with executed versus no-op scope, before U-P5.
3. Human-owned schema decision is required: U2 admits analytic_ops, analytic identity,
   roofline-only results, both grid phases and all-point capture. Fork delegation, full
   hardware configuration, decode-point selection, image identity and actual timing/count
   evidence need an accepted versioned boundary. Preserve existing U2 validators and replay.
4. Resolve exact native stats/count observability, fused prepared semantics, BF16 accumulation,
   dependency pins/licence coverage and missing hardware timing inputs prospectively. Boost
   1.79.0's [BSL-1.0 notice](https://github.com/boostorg/boost/blob/boost-1.79.0/LICENSE_1_0.txt)
   is outside the literal allow-list; PyTorchSim release licence/toolchain closure is incomplete.
   No image licence gate passes from a top-level MIT label. Stats paths/fields require a
   committed prospective supplement before measurements, not post-run normalization.
5. Before runtime edits, write the specified discriminating tests and coordinate exact shared
   interfaces/files with B. Bound support changes still require U0002 human generation/adoption;
   strict currentness cannot be weakened. Independent review is a separate person/session.

Retain existing data by reference: [U2 accepted design](../u2-design.md),
[U2 published validation](U2-published-validation-v1/README.md),
[public demo receipt](U2-public-demo-v1/capture-receipt.json) and the adopted
`contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/` snapshot.
Nominal compatibility is separate from physical G2; no delegation implies mapping equivalence.
The next work depends on the human/administrator prerequisites above. Stop here; no U-P5,
U-P7, fallback implementation, sprint closeout, tag or self-review follows this handoff.
