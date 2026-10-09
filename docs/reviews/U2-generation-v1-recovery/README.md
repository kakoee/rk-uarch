# First generation preserved; wrapper-only continuation

The human first run succeeded: `created: 48 files`. The wrapper then exited at
line29 because ripgrep (`rg`) is unavailable in Javid's terminal. This is a coordinator
wrapper portability mistake, not a generator/inputs change. The second generator
process did not run. The original sealed wrapper and the first logs remain unchanged.

Coordinator read-only checks confirm the frozen package/source/input/environment
identities still match and the candidate passes strict manifest, matrix and current
compatibility validation. Candidate manifest SHA256:
`2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44`.
This is an unadopted first-run candidate; deterministic regeneration is still pending.

The [human continuation](human-continue.sh) preserves the first run, verifies its
exact log/manifest identity, and refuses any existing second-run/audit outputs.
It executes the identical generator command with identical frozen inputs once more
in a new process, then requires verified-identical. Its command-array text has been
compared exactly with the original wrapper, and Bash syntax validation passes.
Log and digest checks use the existing Python interpreter, with no ripgrep dependency.
It then performs the original post-pair preflight, strict/raw inspection and semantic
comparison. No generator/support/input or accepted freeze byte has changed, so the
accepted freeze and first generation remain valid. No new policy approval is needed.

Javid runs:

```bash
bash /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-generation-v1-recovery/human-continue.sh
```

Do not rerun the original script, delete the generation directory or regenerate the
first run. If continuation fails, preserve its files and return the error. No generation
was executed by the coordinator. Adoption, actual-runtime acceptance, commit/push,
final reviews and closure remain separate. Main and worker worktrees are unchanged.
