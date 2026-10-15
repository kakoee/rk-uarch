# Deferred native CI infrastructure and interim local development

**Prepared for human installation.** [Proposed U0024](proposed-U0024.md) records the
multi-sprint local-verification exception and the future runner/registry runbook.
[Recorded authorization](acceptance.md) includes Javid's exact clarification.

The roles are separate: Reza supplies the Linux infrastructure; the actual GitHub owner
supplies repository/package permissions; B constructs and verifies the jobs. A self-hosted
runner does not inherently require the proposed private registry. The chosen delivery route
and current image/tool versions must be rechecked when work resumes.

- [Exact eight-path patch](documentation.patch) and [before/after identities](identity.json).
- [Disposable-export validation](validation.json).
- [Human installer](human-install.sh): --package-commit <commit-containing-this-helper>;
  --check-only performs read-only live checks and applies only in a temporary directory.

Local checks and independent review can support interim development. Remote qualification,
full G5, U9 entry, performance claims and final project closure retain their evidence gates.
This package neither installs the ADR nor changes workflow/runtime/host/registry state.
The live native CI pause remains; existing other hosted checks continue.

Use the concrete command supplied with this package's publication, then return the local
commit receipt. No need to contact Reza or publish an image now. No CI polling is required.
