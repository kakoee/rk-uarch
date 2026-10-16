# Final A source and actual binary audit subject

Final source: **24fa36803081e5077d5977baa91441a2c8534ec8**.
BuildInputs: **sha256:528ade02fc842442f95c6dc54d59c953f7f82cdc3a273a42c7e5cab68cc915ac**.
Private root: **/tmp/u4-k2-candidate-04**. No earlier candidate is relabelled as this build.

| Artifact | Actual SHA256 |
| --- | --- |
| debug executable | 7ed3bad6b96ceb3cf7dfc2d31e69d88b7efbadcccef47810a80728b4a11c6cd5 |
| release executable | ccbbe96853f03e591234885099d47ccea6487787c6061c66777c76f71f1436b4 |
| logical tool inputs | db8b8956f0c060416d0d3c6c11f8eccc6b3ece7433b5075cb093e602febcb73d |
| model source subset | 0bd97d108dd202b5e062196fb86f83ac8664143909eb93ff5a58d400824ba375 |

Both actual library and binary builds pass. Both modes pass45 private library units plus
133 complete admission-only inputs and48 B exact canonical/refusal DTOs. Both actual binaries
pass11 frozen invalid-input/argument controls. All-target clippy and pinned cargo fmt --check
pass. The debug target had its clippy preparation before the binary build; the release build
used a fresh separate target. These are actual construction observations, not timing claims.
The ignored tests were explicitly selected and each ran one nonempty bounded loop.

B: use these explicit inputs and source, rather than candidate-03. The same published
build_candidate.py prepare/build commands apply with candidate-04/BuildInputs.json and a
fresh private root. The exact ordinary commands/environment are in observations/commands.json;
wrapper/link-map and raw command inventories bind private originals. Both executable digests
must match independently in the approved diagnostic experiment. No new tools/dependencies,
flags, security settings, public success jobs or acceptance record are needed to audit this
candidate. The declaration/observation limits are in ../read-boundaries.md.

A has not run the B tracer. Final candidate-specific B reads, Python generator/read closure,
independent review, runtime deployment and exact human first-use subject remain pending.
The first-use-subject.json is concrete; HostRecord-proposal.json and HostSelector-proposal.json
leave required real authority fields absent. They cannot be used as qualifying records.
