# Staging recovery — correct output placement, preserve guard and source

The first human staging attempt failed after preflight with `unreviewed import name: tables`.
This was a coordinator helper bug: it created a new importable root namespace in frozen A,
then the selected policy correctly refused that namespace during inventory. The old read-only
preflight did not exercise directory creation and missed this interaction.

Inspection found only `tables/U4-M-policy-input-freeze-v1/`, empty: no inputs, manifest,
receipt or oracle result had been created. The exact empty tree was renamed, without deleting
anything, to the coordinator's ignored `tables/U4-M-policy-staging-failed-attempt-v1/`.
[Observed failure and preservation](failure-and-recovery.json). A's source commit and all
tracked bytes remain unchanged. The policy guard, support inventory and generator are not edited.

The corrected helper creates its output outside A, under:
`/home/jjaff/AI-infra-simulation/rk-uarch/tables/U4-M-policy-input-freeze-recovery-v1`.
All source/policy/environment/input requirements are identical. It verifies that only output
placement differs from the approved source specification. The original approval at
`28fd452f33f8b24ba8796451bd1e758b4c885aa6` remains the authority for the same human input-staging
operation. Recovery changes storage placement to fix that authorized operation; it is not
represented as a new human policy vote or an approval of generation/adoption. Use the newly
pinned recovery helper, not the historical helper or its failed output path.

No agent runs the staging producer. The human command still requires UARCH_HUMAN=1 and exact
package/approval pins. Check-only prepares no inputs, and the helper refuses existing output
rather than overwriting or resuming it. On success it returns the actual input digest for
coordinator freeze review. No frozen-input acceptance, oracle run, adoption, commit, push,
K2 work, infrastructure or qualification follows from this recovery.

Regression checks exercise the real installed import guard and support inventory across
output-directory creation in private source exports. They reproduce the old failure,
confirm the corrected outside-source placement, and check path refusal before creation.
Their details are recorded separately; no real inputs are staged by those checks.

Executed regression selection: **4 passed** in disposable exports; Ruff passes for the helper
and tests. The cases reproduce the old guard refusal, verify the corrected layout against
all 56 actual dependency entries, refuse a source-local output before writing, and preserve
an existing output's sentinel. No input producer or oracle was executed. The corrected
helper's pinned check-only result will be retained in a separate receipt.
