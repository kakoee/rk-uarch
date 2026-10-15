# U4-M-and-K1-release-v1 — decision for Javid

**PROPOSED. No approval is recorded.** B's final reconciliation is published at
`1a56ff22068ded35cac944fd8c1de8ffde9cc86d`. The coordinator's bounded check and limits are
in [checks.md](checks.md). No architecture decision is being reopened.

## D1 — exact M schema and trust mechanism

Accept A's 26-path M patch, SHA256
`d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`, and the eight
[encoding decisions](../U4-A-M-package-v1/decisions.md) at `111b24b`.
This defines the data the native engine will consume and return, including how approved
profiles and clocks are distinguished from a caller's self-consistent but unapproved input.
Use separately held host hashes bound to your exact published Git acceptance record.
Actual qualifying profile/registry/engine hashes remain separate first-use decisions.

Authorize preparing the combined installation/freeze of these bytes and the already
selected U0002 repair. This does not run generation, adopt an unseen candidate or install
protected files. Those concrete human steps remain separate. The 56-file result is an
audit of this source, not a guarantee that later dependencies cannot change it.

## D2 — exact K1 tools/licences and implementation release

Accept A's [exact tool and licence text](../U4-A-toolchain-v1/proposed-ADR.md) at
`83a9a14fd76a00b7858ddd140cc0e0589f80a267`:

- Rust 1.99.0 on x86_64-unknown-linux-gnu with the pinned fmt/clippy components;
  exact serde, serde_json, proptest features and all 27 locked external crates.
- The Unicode-3.0 exception for **unicode-ident 1.0.27 only**, at its recorded checksum;
  no global licence exception. The private-workspace setting invents no project licence
  and exempts no external registry dependency.
- Pinned cargo-deny and the pinned Linux build/test image inputs. Run-only compiler/OS
  obligations stay distinct from engine dependency permissions. No public image
  distribution, static glibc linking or waiver of obligations is approved.

After the human ADR record is installed, release A's private K1 Rust kernel/tests and
B's disposable environment/offline-cache/discovery work. K1 can proceed independently
of M installation. B freezes real test names and the built image identity from actual
results; no native pass is claimed now. Private registry/image distribution, if needed
for hosted CI, requires a concrete destination/access proposal before publication.

## Exact record and sequence

The proposed [one-file ADR patch](protected-adr.patch) records D1 and D2 in U0011; its
[before/after identity](adr-identity.json) binds the exact bytes. It is unapplied.
Existing U0011 text is preserved; this addendum supplies the previously missing exact
schema/tool choices and bounded U4 release.

1. Javid approves D1, D2, or both and the corresponding exact record. If only one is
   approved, prepare its isolated patch before human installation.
2. Human installs the approved protected ADR record through normal ownership. Then
   A can start private K1 and B can construct/check its environment within D2 scope.
3. In parallel, coordinator prepares the exact M/policy installation and frozen input
   package for the separate human lifecycle. No half-migrated main is published.

Approval does not close M, K1, G3a or U4, qualify native results, release K2/model work,
authorize oracle generation/adoption, or establish hardware/performance evidence.
The CI proposal and all fixtures remain subject to their actual execution/first-use checks.
