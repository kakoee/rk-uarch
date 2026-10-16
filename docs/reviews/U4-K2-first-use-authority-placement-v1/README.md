# K2 first-use authority placement

The existing `U4-K2-deployment-and-first-use-v1` approval covers this step. The
human sealed runtime was reverified, and the authority-free container preflight
passed. Actual evidence and genuine approval are published at
`cc91e5489a58e06addb2f43e45a0e4e71cb66aa1` in
[the authorization record](../U4-K2-first-use-authorization-v1/README.md).

B's unchanged publication verifier from
`f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f` verified all four published blobs,
reviewed HostRecord fields, subject, package and successful preflight. Its exact
selector and runtime-release objects are serialized in `payload/`. The other
three payload files are unchanged published bytes. [placement.json](placement.json)
binds all five destinations and digests.

Run `human-place.py` as the existing user with `--helper-commit <this published
package's full commit> --place`. It first verifies the published helper/package,
original sealed deployment and exact authority objects. Only then does it request
sudo to add five new files and two new directories. It embeds verified bytes in the
root shell command rather than running user-owned Python as root. It refuses
existing destinations. New files are root:root 0444; new directories are 0555.
Existing files, symlinks and directory identities must remain unchanged. Nothing
is written to host `/etc`, and no engine job runs from this helper.

Without `--place`, verification is read-only. A partial placement stops for
reconciliation; rerunning cannot overwrite it. The helper writes its successful
receipt to `tables/U4-K2-first-use-v1/human-authority-placement.json`.

Checks executed here: real read-only placement preflight; exact published authority
verification; Bash syntax; missing, extra and substituted destination refusals;
scoped Ruff. See [checks.json](checks.json). Root installation is not tested or
claimed as performed by the coordinator. Construction/native suites are reused,
not rerun.

After the human returns the receipt, existing approval covers B's unchanged
798-call public campaign and saved-result replay controls. Runtime failure stops
that sequence. U0024 deferrals and later qualification boundaries remain unchanged.
