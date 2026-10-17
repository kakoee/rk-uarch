# Approved combined runtime — human documentation and payload placement

Javid's genuine `yes` is published at
`026d365e0bee9da1ff1ea1a8717e12ab1dfe23e8` in
[decision.json](../U4-K2-combined-runtime-authorization-v2/decision.json).
No new approval is requested. The reviewed candidate/helper remain ecc0dfaf / 0c4afcfa.

The reviewed renderer independently verified actual remote publication and prepared all 40
payload files. The first preparation attempt refused a moving remote main; a second attempt
with unchanged approved pins succeeded. No placement or native execution occurred. The
failed diagnostics are retained under /tmp/u4-k2-approved-v2-render-logs; compact identities
are in [preparation.json](preparation.json). [publication-check.json](publication-check.json)
records the successful actual remote observation and exact blob reads.

[installation.json](installation.json) pins the two reviewed ADR patch pre/postimages and
the exact rendered /tmp/u4-k2-approved-placement-v2/human-place.sh bytes. All payload hashes
match [postimages.json](postimages.json); shell syntax passes. This wrapper installs no
runtime source into the checkout and changes no canonical generator/support/artifact bytes.

Run human-install.py with its published full helper commit. Default mode is read-only.
With UARCH_HUMAN=1 and --install it:

1. Verifies helper/approval/patch/script bytes, exact HEAD/main, clean tracked tree/index,
   normal hooks and identity, no unfinished Git operation, safe parents and absent new root.
   Existing unrelated untracked reviewer files are preserved and never staged.
2. Applies only the two approved ADR documentation patches, verifies/stages their exact
   bytes and commits with normal human-owned/frozen-prediction hooks. No push.
3. Passes the already hash-verified placement script bytes to sudo /bin/sh via stdin;
   it does not execute a mutable user-writable script path as root. Javid enters the sudo
   password in the terminal. Exactly 40 files are placed root-owned/read-only under
   /var/lib/rkuarch/k2/candidate-04-combined-runtime-v2. Existing deployment is untouched.
4. Verifies exact file/directory membership, hashes, ownership, modes and empty authority;
   prints documentation and placement receipts, then stops.

The original prospective wording is preserved exactly as reviewed in the installed ADR
addendum; the genuine decision above records its acceptance. No proposal bytes were silently
rewritten after review. Component ADR changes must retain this addition when later installed.

If any step fails, retain the printed receipts and partial state. Do not delete, resume,
retarget or overwrite a partially placed root. Return the error for reconciliation. If the
prepared /tmp script is missing or changed, the helper refuses; the coordinator can regenerate
preparation with the same approved pins. Human root placement is not performed by an agent.

After the human receipt, existing approval covers coordinator publication of the local ADR
commit, actual authority-free preflight, and subsequent genuinely bound selector placement
and campaign/replay sequence. Payload placement does not install authority, run a native
job or establish qualification. Real preflight must verify the mount-source assumption.
