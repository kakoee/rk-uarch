# Lane B — bounded F5 correction after Stage 3

This is B's author response for the same reviewer's focused F5 recheck. It adds two ordinary
unit tests in **one new test file**, plus this disposition/evidence addendum. Production,
checker, carrier, clock, schema and normative-text bytes are unchanged. The correct reviewed
implementation already rejected the attack. No independent acceptance or closure is claimed.

The [coordinator report identity](../U4-component-F5-correction-v1/checks.json) and its preserved
review evidence are bound in [inputs.json](inputs.json). Prior A/B packages and reviewer
originals remain untouched. Stage 3's acceptance of F1–F4 and F6–F11 is inherited; the completed
F6 experiment is preserved without repetition.

## Correction and discrimination

At 1 GHz, the two-hop D01 response requires four cycles, so a grant at **55000 ps** must
complete at **59000 ps**. The consistent attack changes its end and clock completion to
**58500 ps**, keeps `n_cycles=4`, and extends the following receiving alignment to
[58500, 59000). Port service remains [59000, 60000); request/job completion, useful work,
traffic and makespan remain unchanged. Joined resource/queue/event/critical witnesses are
synchronized and the result is resealed. These are explicitly synthetic unit carriers.

The new `test_d01_response_duration_control` passes both real `validate_result` and B's
`check_v2`. `test_d01_clock_consistent_response_duration_forgery` requires structural admission
and exactly `CheckFailure: mechanism duration` from B. It fails on an alternate refusal.

[Restoration receipt](restoration.json) records the executed sequence:

| State | Result |
| --- | --- |
| New valid and forged controls, intact candidate | 2 passed |
| Delete ONLY the `mechanism duration` guard | 1 passed, 1 failed with **DID NOT RAISE** |
| Reviewer's unchanged probe with that single guard removed | Valid and forged carriers accepted by both layers |
| Old duration test with that single guard removed | Alternative `clock mechanism binding` refusal; **not** an unsafe-acceptance kill |
| Restore exact source bytes; rerun new controls | 2 passed |
| Affected checker selection, once | **49 passed: 47 behavioral + 2 identity** |
| New-file collection under ordinary config and CI marker filter | 2 collected |

The affected selection is the new test file, the unchanged 45-test
`test_consistent_observations.py`, and the two existing selection identity tests. Identity
checks never count as behavioral kills. The new test passes strict mypy; applicable lint
passes. Every counted Python probe/test uses an explicit private root/config and verifies
loaded project module origins. [Checks](checks.json) distinguish new execution from inherited
evidence; [evidence archive](evidence.tar.gz) retains logs and their [membership hashes](evidence-manifest.json).

The old matrix's claim that duration is jointly defended by duration and clock witness is
**retracted for consistent forgeries**. The clock join checks truthful work and joined
completion, but does not independently enforce elapsed mechanism time. The old test's
`n_cycles=2` against one-cycle work is masked by that join. The new
[matrix addendum](matrix-addendum.json) classifies `mechanism duration` as essential and
supersedes only that duration disposition and the coverage overstatement. Earlier receipts
remain historical evidence, unchanged.

## Exact additive proposal and reconstruction

[proposal.json](proposal.json) binds the ordered pair:

1. Original combined patch `81b81c6c2680a17e7d106dedb4a11dc07891b331f3323319fb0192b852bdebe3`,
   on preparation base `414a94c35c1588cf13b6fcddc3739203c7f5ec6e`, using the exact reviewed A
   manifest `5d1010aac38f7d04a2935ff48072e418e1e8e9a88d1933758fca4581e2acc845`.
2. [Additive test patch](test-only.unapplied.patch)
   `23724b209c73fcfb55c62836570a296817936137111a00dfd2f51862ea0757f3`.

The sole added postimage is `validation/component/test_f5_mechanism_duration.py`, SHA-256
`e4f9f8693f20031ccf8b97d24a141b0aa63725e220fb6a754d2275cb5c6b0f8a`.
There are 24 effective postimages: all 23 reviewed postimages plus this file.

The original 106-case selection remains exactly
`sha256:4b9e73cf9ef11456e216acba58c9496c242169e2a40efcf0aa9e3f36bf0dbbc0`
(file SHA-256 `a8b94f0d83f429e5101b2b62ba5ed91d9b98d0d228330f5185acc37aab29319c`).
No case/input bytes, policy or authority change. Its existing fingerprints remain valid
because none of its bound files changes. The supplemental proposal explicitly adds the
new test binding and patch ordering; **the old selection alone does not bind the added test**.
Field-level additions are recorded in `proposal.json`; no original manifest or selection is
rewritten. A-owned aggregate metadata does not need a round trip for this B-only addition.

From this checkout, with the existing Python 3.12 environment (adjust only `PY` to its actual
path), reconstruct in a **new** private directory:

```sh
PY=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
$PY -I -B docs/reviews/U4-B-component-F5-correction-v1/reconstruct.py /tmp/component-f5-review
$PY -I -B docs/reviews/U4-B-component-F5-correction-v1/isolated.py /tmp/component-f5-review pytest -q validation/component/test_f5_mechanism_duration.py
```

The reconstruction verifies the original helper/manifest/patch, nine activation inputs,
consumer sidecar, all 23 old postimages, then applies the one-file delta and verifies its
hash. This exact ordered reconstruction was executed and hash-checked. It uses the historical
preparation tree. **Do not apply the old U0011 postimage to current main**: current accepted K2
coexistence clauses remain intact and later human installation must reconcile the text.

For a focused recheck, extract the coordinator's `review-evidence.tar.gz` into a new private
review directory. Then `fault_control.py PRIVATE_EXPORT REVIEW_DIR/stage3/probe_f5_duration.py
NEW_LOG_DIR` executes only the sequence above. It removes one exact guard statement, restores
in `finally`, excludes fingerprints from kill scoring, and reruns affected checks. No broad
488 selection, F6 repeats, guard sweeps, K2/native campaign or full suite is needed.

## Observation triage and remaining dependencies

**O1:** all eight named sub-guards receive an explicit **independent discriminating coverage
not demonstrated** disposition in the matrix addendum. The inherited single-removal survivors
are not proof of redundancy. Parent F1/F2/F8 acceptance stands; this wording correction creates
no additional adjudicated finding and claims no new sweep.

**O2:** [B-U4-OBS2-TRANSIENT-LIFETIME-01](obligations.json) is owned by B and pending before
reliance on the `/2` transient @2 lifetime branch at component native first use, or an explicit
scoped disposition at that boundary. It requires an independent transient positive control
and a consistent discriminating negative. No unsafe case has been established; C02's
persistent-accumulator control does not satisfy it. It is not a dependency of this bounded
F5 test correction.

**O3:** F6's completed random-revert result remains inherited and intact. Future harness
optimization stays in the separately queued verification-runtime plan; no historical script
or outcome is relabelled.

There is no unresolved A dependency or production fix for this correction. The same reviewer
still must perform the focused F5 recheck. Existing human semantics/profile decisions, U0011
reconciliation/protected installation, actual L1 workings and future component execution
identities/authority remain separate. No pin/licence decision is reopened. No protected
installation, native build/run, production authority, semantic acceptance, G3a or U4 closure
follows; current K2 runtime and evidence remain unchanged.
