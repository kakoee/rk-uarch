# Proposed U0011 addendum — exact U4 K1 tools and scoped licences

Status: PROPOSED exact text for human installation; no protected ADR is edited.
Coordinator binds the final published U4-A-toolchain-v1 commit and package identity.

> For private K1 correctness work, accept Rust 1.99.0 for
> x86_64-unknown-linux-gnu, minimal profile plus rustfmt and clippy, at the compiler commit,
> manifest and component checksums in U4-A-toolchain-v1/pins.json. Accept the exact
> serde=1.0.229, serde_json=1.0.154 and dev proptest=1.12.0 requirements, disabled defaults,
> enabled features and full Cargo.lock/checksum closure in that package. These are the only
> direct kernel dependencies; transitives are admitted only at the locked identities.
>
> Accept Unicode-3.0 solely for unicode-ident 1.0.27, whose licence is
> `(MIT OR Apache-2.0) AND Unicode-3.0`, with its recorded crates.io checksum and retained
> notices. Select MIT for its alternative permissive arm. This exception admits the Unicode
> identifier tables reached through serde_derive/proc-macro2/syn. It does not add Unicode-3.0
> to a global allow-list, cover future versions, or admit another dependency. A changed
> version, checksum, licence expression or feature closure requires renewed review.
>
> Accept cargo-deny 0.20.2 at the official musl binary digest in cargo-deny.json as a run-only
> verification tool, and the exact deny-proposed.toml policy. Its private-workspace exclusion
> covers only publish=false first-party packages; it grants no licence to rk-uarch and
> exempts no external registry dependency. All external crate licences remain checked.
>
> Accept the exact Linux amd64 official Rust container manifest and OS package bytes in
> container.json/os-packages.json, with the recorded copyright notices, solely as the private
> build/test environment. The exact Dockerfile.engine.proposed adds only checksum-verified
> fmt/clippy and cargo-deny tools. GCC/binutils and Debian utility GPL licences, glibc LGPL
> and GCC runtime exceptions, and the compiler/tool distribution's recorded licences are
> acknowledged as build/run environment obligations, distinct from the permissive engine
> crate allow-list. Retain all installed copyright notices and corresponding upstream source
> references. This is not approval to modify/distribute those components, publish this image,
> link glibc statically, or waive any licence obligation. Distribution or new components
> require a separately scoped review. cargo-deny covers crates, not this OS/tool inventory.
>
> These decisions release private K1 implementation and correctness checks after normal
> task authorization, independently of M. They approve no native result, public K2 admission,
> host provisioning, performance budget/claim, hardware expenditure, or artifact generation
> and adoption. Before K1 evidence counts, Lane B's real Linux CI uses these same exact pins.
