# U4-K1-installed-inventory-v1

Approve installation of B's exact two-path
[inventory-bindings.patch](../U4-B-K1-installed-inventory-v1/inventory-bindings.patch),
reviewed from proposal commit `c41499458307836484efdeb587a6c8bd4c5c910f`.

Patch SHA256: `4b807f41653a33e1a7e29ed840ce0f55e4d3313da10c91791142bf2a781c070d`.

1. Replace `.github/native-k1-tests.json` with the tested 28-name inventory,
   SHA256 `e2a7bf61a71dce69485765a76759d4add7bbe5ada11ddd3a0b179742c253be46`.
2. Add `.github/native-k1-controls.json`,
   SHA256 `6df76826563a61caa208c8619f6ef35dda74a5122e03bcd2000a9603229e98ef`.

The inventory retains actual tested source `fb7ba4a75d17650d91c2d2532460ccc1c16b5808`
and replay SHA256 `4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a`.
Fault evidence retains its actual source `63ca8bec5a4ac1d7dcf87290a5cf080c846de66d`.
The old 19-test inventory remains available through Git and its historical receipts.

After approval, verify the unchanged patch and preimages, install only these two paths,
and validate the installed bytes against the reviewed candidates. Make a separate local
commit with normal hooks: `chore(native): bind installed K1 inventory and controls`.
Then perform a separate normal push and record the remote commit, preserving peer history.
This decision authorizes those sequential actions; it does not combine commit with push.
Do not rerun native campaigns absent a concrete change or missing evidence, and do not
poll hosted CI.

This replaces data bindings only. No runtime changes, hosted job activation, image
publication, remote/performance qualification, K2 release, sprint closure or tag is
authorized. The separate inventory decision was reserved explicitly in the prior
approved installation/formatting scope and the B task; the accepted K1 code and formatting
are not being submitted for approval again.
