# Owner action: approved exact private K1 image and main-only access

Publication **is approved**. Javid will arrange owner involvement; no further pin, licence
or publication vote is requested. These are owner-run instructions, not completed operations.
Use the existing local Docker daemon on Javid's workstation, where the verified image exists.
Do not transfer the image to a second destination or rebuild it.

| Item | Exact value |
| --- | --- |
| Namespace owner | `kakoee` (personal account) |
| Existing local tag | `rk-uarch-k1-builder:u4-b-e9f69f414983` |
| Verified local image ID | `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523` |
| Approved publication tag | `ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee` |
| Visibility/access | Private; independent granular ACL; no repository Actions/Codespaces grant |
| Repository environment | `kakoee/rk-uarch` → `native-k1-private` |
| Deployment selection | Selected branches and tags: **Branch `main` only**, no tag/wildcard/PR rule |
| CI identity/secret | Username `kakoee`; separate `K1_GHCR_READ_TOKEN`, classic `read:packages` only |
| Native selection | `.github/native-k1-tests.json`: 19 tests once per mode, six private replays |
| Final registry identity | Must come from successful publication/readback; no substituted base digest |

## 1. Owner UI preparation

Sign in as `kakoee`. In [Packages](https://github.com/kakoee?tab=packages), inspect any existing
`rk-uarch-k1-builder`. In **Package settings**, verify private visibility, independent access
and no **Manage Actions access** or **Manage Codespaces access** repository grant. Do not
connect `kakoee/rk-uarch` or inherit its public-repository permissions. Stop if an existing
public package or conflicting tag prevents this exact operation; do not replace it.
A 404 from `jjaffari` does not establish absence. The helper authenticates as the owner and
lists all owned container packages before deciding whether this is a new publication.
[GitHub package permissions](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

Create an expiring classic publisher PAT from
[the write:packages-only creation link](https://github.com/settings/tokens/new?scopes=write:packages).
Use a descriptive name such as `rk-uarch K1 one-time publication`, select an appropriate short
expiry, and verify **no `repo` or `delete:packages` scope**. Implied `read:packages` is allowed.
Keep it in the owner's password manager. Separately create an expiring classic PAT from
[the read:packages-only link](https://github.com/settings/tokens/new?scopes=read:packages),
named for `native-k1-private`; select only `read:packages`. The helper refuses broader scopes.
[GitHub registry authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

No account upgrade, payment method, budget increase or other spending is part of these steps.
GitHub currently lists Container registry storage/bandwidth as free; verify that still applies
when the owner performs the operation, and stop if payment is required.
[GitHub billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages).

## 2. Publish the existing image from a trusted local terminal

Run in the independent B clone. These commands contain no token. `owner-registry.py` prompts
on the terminal with echo disabled; do not run it under a terminal recorder or give a token
as a command argument. The script uses Python's standard library and existing Docker only.

```bash
cd /home/jjaff/AI-infra-simulation/rk-uarch-u4-b
git pull --ff-only origin main
K1_OWNER_RECEIPTS=$(mktemp -d /tmp/u4-k1-owner.XXXXXXXX)
python3 -B docs/reviews/U4-B-K1-private-ci-v1/owner-registry.py \
  publish "$K1_OWNER_RECEIPTS/publish"
```

At the hidden prompt enter the **publisher** token. The helper verifies the authenticated
owner and scopes, private package state, existing tag identity, exact local image and platform.
It logs into a temporary Docker config, performs precisely:

```bash
docker --config "$K1_TEMP_CONFIG" tag \
  sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523 \
  ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee
docker --config "$K1_TEMP_CONFIG" push ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee
```

These two lines explain the helper's exact actions; `K1_TEMP_CONFIG` is internal, so use the
helper rather than running the excerpt. It then pulls the published tag, verifies image ID
and layers, checks private visibility through the API, and writes the actual GHCR digest to
`publish/result.json`. Docker credentials are deleted when the helper exits normally or with
an exception. No publisher credential is put into GitHub Actions or the repository. After a
failure, inspect receipts and owner UI before retrying; a failed push/readback can leave a
published package. Do not interpret failure as proof that nothing was uploaded.

Immediately revisit **Package settings**: record private visibility, independent ACL and empty
Actions/Codespaces grants. The exact image inherits
`org.opencontainers.image.source=https://github.com/rust-lang/docker-rust` from its base;
this is upstream metadata, not the final builder identity. Inspect **Repository source** and
whether any link/inheritance was actually created. Do not assume that a source label proves
an access grant or that private visibility alone proves independent access. If the resulting
ACL is broader than approved, stop activation and report the observed state; do not silently
change the image, broaden grants or claim successful private access.
[Repository linking and source labels](https://docs.github.com/en/packages/learn-github-packages/connecting-a-repository-to-a-package).

## 3. Verify the separate reader and configure the environment

Still in the same shell, extract the **observed** registry identity and test it using the
separate reader token at the hidden prompt:

```bash
K1_REGISTRY_IMAGE=$(python3 -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["registry_image"])' \
  "$K1_OWNER_RECEIPTS/publish/result.json")
python3 -B docs/reviews/U4-B-K1-private-ci-v1/owner-registry.py \
  check-reader "$K1_OWNER_RECEIPTS/reader" --digest "$K1_REGISTRY_IMAGE"
```

This proves a private pull with the reader credential on the local daemon. It is not hosted
CI evidence and does not prove GitHub received that same secret. Keep the reader token in the
owner's password manager for expiry/rotation; revoke the one-time publisher token after the
publication and ACL checks succeed. The reader token is account-scoped, as approved.

Open [repository environments](https://github.com/kakoee/rk-uarch/settings/environments).
Choose **New environment** → `native-k1-private` → **Configure environment**, or inspect that
exact environment if it already exists. Under **Deployment branches and tags**, choose
**Selected branches and tags**. Add one rule with **Ref type: Branch**, pattern **`main`**.
There must be no tag or other branch rule. Preserve unrelated settings; report conflicts.
Under **Environment secrets** → **Add secret**, set **`K1_GHCR_READ_TOKEN`** to the separate
reader PAT through GitHub's secure UI. Do not create a repository-level secret. No environment
variable is needed: the template fixes the reader username to `kakoee`. Do not add a broader
repository package grant to make authentication work.
[GitHub environment setup](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

The owner's existing authenticated GitHub CLI can capture non-secret settings after the UI
work. Do not add repository scope to either package token for these commands:

```bash
gh api repos/kakoee/rk-uarch/environments/native-k1-private \
  --jq '{name,deployment_branch_policy,protection_rules}' \
  > "$K1_OWNER_RECEIPTS/environment.json"
gh api repos/kakoee/rk-uarch/environments/native-k1-private/deployment-branch-policies \
  > "$K1_OWNER_RECEIPTS/branch-policies.json"
gh api repos/kakoee/rk-uarch/environments/native-k1-private/secrets \
  --jq '{total_count,secrets:[.secrets[]|{name,updated_at}]}' \
  > "$K1_OWNER_RECEIPTS/secret-names.json"
```

Expected: `protected_branches:false`, `custom_branch_policies:true`, exactly one branch
policy `{name:"main", type:"branch"}`, and the named environment secret. Its value is never
retrievable through this API. A 404/403 is a failed access check, not proof of correct setup.
[Deployment branch API](https://docs.github.com/en/rest/deployments/branch-policies).

## 4. Return non-secret receipts for the final installation

Return `publish/result.json`, `reader/result.json`, the three environment metadata files,
and the owner's factual package-ACL observation, reader expiry date and time of the UI checks.
Never return PAT values, Docker config files or credential-store contents. Preserve failed
command receipts locally; share only reviewed, non-secret diagnostics.

The prepared [native job](../U4-B-final-reconciliation-v1/native-job.yml.in) still contains
one explicit unresolved registry digest. Once the receipts and ACL state are checked, B can
replace that field with `reader/result.json`'s `registry_image`, replace only `jobs.native`
in `.github/workflows/ci.yml`, and publish with normal hooks. The job runs only trusted pushes
to `refs/heads/main` when `docs_only != 'true'`, references `native-k1-private`, and keeps
host Python guards separate from offline container tools. Its temporary pull credentials are
removed before native execution. No executable job containing placeholders is installed.

The existing Markdown classifier stays unchanged. Hosted execution, fork-PR native access,
independent review and qualification remain separate evidence requirements. A skipped PR job
is not a native pass. No M installation, policy repair, artifact lifecycle, human L1 signoff
or sprint closure follows from this owner handoff.
