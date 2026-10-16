# Candidate-03 audit subject — superseded by final lint correction

The final all-target clippy command subsequently found `items_after_test_module` in
hardware.rs. Its private test module is moved to the end without runtime behavior changes.
Candidate-03 source/inputs/binaries and refusal/private test observations remain preserved;
use the later candidate-04 subject for the final audit.

Retained source subject: **3888fb25e46fd63a0763d3c1054f46e586e7b28d**. Subsequent evidence
commits do not change its explicit source inventory. candidate-03/BuildInputs.json hashes
to **sha256:365029351e5c81bdcbf83ba509e417cc3912cfd7afca1388b724a932c0bebc7e**.
The 73-file declared source inventory, both modes, pure generator, engine-free BuildTrust
and actual ToolInputs are bound there. The source is published, not an untracked input.

Actual A ordinary builds, /tmp/u4-k2-candidate-03:

| Mode | Actual executable SHA256 |
| --- | --- |
| debug | 9d08b7d20b37d4be4f29f52b2396404c8fbdff8c07c3c2e2b4f2aae2659bbb23 |
| release | 857de449fa8de7b0452ab26d8043a73e947027bdc96c98b1830045332d4aee95 |

Both modes pass45 private library tests plus the two explicitly selected ignored tests:
133-case complete DTO admission-only loop and48-case B exact canonical/refusal loop.
Both actual binaries pass11 frozen invalid-input/argument controls. These are newly observed
construction checks; no complete public mapped job was executed. The133 pending complete
requests use the real logical identity, with maximum2,116,641 bytes; all are below64MiB.
The266 debug/release public cases are authored and collection-only, pending human authority.

To reproduce in a fresh private root with the accepted readonly cache:

```
.venv/bin/python native/tools/build_candidate.py prepare --scratch FRESH --inputs docs/reviews/U4-A-K2-construction-v1/candidate-03/BuildInputs.json
.venv/bin/python native/tools/build_candidate.py build --scratch FRESH --mode debug
.venv/bin/python native/tools/build_candidate.py build --scratch FRESH --mode release
```

Exact actual Docker commands/environment and compiler/linker argv are retained privately;
the consolidated observations will publish their compact hashes/commands. Controls are
fixed /controls paths, source /work, separate private /target per mode, C2_RUN_TAG=construction,
unchanged flags and mode-specific link maps. A normal cold build and B's traced cold build
must compare both actual binaries; traced reads do not inherit from c678ded's probe.

B: retest the corrected48 vectors and audit both exact candidate builds under the existing
approved canary/trace limits. Reconcile source/includes/generated identity, config absences,
cache/tool/OS/process/fd/cwd/mmap/exec and environment limits honestly. The initial Python
freezer/generator imports and input selection also need an explicit bounded read inventory;
the Cargo descendant trace alone cannot establish those. A's declared73 files are an input
manifest, not an observed exhaustive read list or an automatic quota. Review exact133 saved
job/case/outcome membership (now enforced in the Python resolver) and the actual final subject.

First-use remains dependent on real B review, exact human subject, commit/blob installation
verification and immutable executable/runtime loader/DSO deployment. No selector, final
HostRecord, accepted decision or placeholder hash is created by this source freeze. A's
receipt read-status stays partial until the candidate-specific B findings are published.
U0024, C3, qualification and successful public execution remain separate.
