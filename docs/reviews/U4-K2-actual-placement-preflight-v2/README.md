# Actual immutable placement and authority-free preflight

Human documentation commit da895b94e91992f6fa2318b16fbc48d5c8341b89 has exactly the two
approved ADR postimages and the expected parent. It was published through normal main
integration without changing peer preparation. Independent checks verified all 40 placed
payload files, exact membership, root ownership/read-only modes and empty authority.

The exact reviewed launcher at helper 0c4afcfa executed the REAL preflight in the accepted
local image, using the placed v2 root and original sealed native source. Exit 0, complete,
about 4.03 seconds outer launch time. This is import/deployment verification, not authority
resolution, simulator execution or performance qualification. Both authority selectors were
absent from the preflight container; its process-creation guards were active. Native calls: 0.

[Reconciliation](reconciliation.json) hashes the actual full receipts. The reviewed
check_preflight accepted the observed sealed inventory, module/helper origins and mount
sources. O-S3-3's filesystem assumption holds for the actual /project, /combined and
/combined-record mounts. The expected exact roots were observed read-only; no private
receipt was substituted. Original bindings remain valid and the new authority is still empty.

[placement.json](../U4-K2-combined-runtime-authorization-v2/placement.json) binds this genuine
preflight to the already published human decision. Its publication enables the reviewed
five-file binding renderer. Root-owned selector/release placement remains a human action;
the campaign may start only after that placed authority passes the existing checks.
No new policy approval is needed. No campaign/replay, component execution or closure occurred.
