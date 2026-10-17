# Approved K2 authority placement v2

The actual authority-free preflight passed and is published at
`b11bf3add519085608adb9f69d2969423de65fd6`. The reviewed renderer fetched the real remote
and generated these five authority files from that placement record and Javid’s published
approval `026d365e0bee9da1ff1ea1a8717e12ab1dfe23e8`.

This is the already-approved human root step. `human-place.py --helper-commit <full published
commit>` verifies only; add `UARCH_HUMAN=1` and `--place` for human placement. The helper
accepts later main commits only while its exact package and pinned inputs remain unchanged.
It requires the original sealed 40-file payload and empty authority, verifies the prospective
five-file binding without resolving any host, then sends only hash-verified in-memory script
bytes to sudo. It verifies the resulting 45-file seal and reports the exact binding.

The script refuses existing authority files; it does not overwrite or repair partial placement.
Return any failure for reconciliation. No runtime launch, generation, Git mutation or campaign
retry is performed by this helper. After the human receipt, the coordinator can perform the
already-approved fresh 798-call campaign and required replay controls. The old 88/89 stopped
run remains historical and supplies no slots to the new campaign. U0024 remains unchanged.

See [placement identities](placement.json), [authority postimages](authority-postimages.json),
[actual remote read receipt](publication-check.json), and
[actual preflight](../U4-K2-actual-placement-preflight-v2/README.md).
