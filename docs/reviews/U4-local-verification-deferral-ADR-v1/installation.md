# Human installation

Direction is already approved. The human-owned paths still require Javid's installation
under CLAUDE.md. The exact package is committed at
`9d45f0564c8854285c4564967b6d48f760c94d94`; the installer also accepts later HEADs when
its package and target before-images are unchanged. Preserve unrelated untracked reviews.

```bash
cd /home/jjaff/AI-infra-simulation/rk-uarch
UARCH_HUMAN=1 bash docs/reviews/U4-local-verification-deferral-ADR-v1/human-install.sh \
  --package-commit 9d45f0564c8854285c4564967b6d48f760c94d94
```

This installs the ADR and seven synchronized documentation updates, then makes one local
commit through normal hooks. No push, CI activation, image publication, server change,
M installation, artifact lifecycle or K2 release occurs. Return the receipt for verification.
No new approval of the already accepted policy direction is requested.

Validation: 36 focused tests (including prompt synchronization), strict artifact currentness,
eight exact postimages and ADR local links passed in a private export. Installer read-only
preflight passed live and in a disposable clone; missing human flag and invalid ancestor
refused; scratch staging matched exactly eight files and had no whitespace errors.
See [test receipt](validation.json) and [installer receipt](installer-checks.json).
No full suite, native execution or remote CI was run for this documentation-only package.
