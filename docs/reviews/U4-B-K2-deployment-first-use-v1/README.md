# Candidate-04 deployment and first-use approval package

Recommend the **existing accepted local image**, with the existing Python runtime mounted
read-only into the same container as the two verified native executables. The image has
no Python on its configured PATH. No new image, package acquisition, registry or server
is needed by this proposal. Relocated Python imports/ABI remain a mandatory, authority-free
preflight after approval; static inspection cannot establish that they execute successfully.

This package completes deployment preparation; it does not reopen the reconciled
[candidate-04 construction audit](../U4-B-K2-candidate-04-audit-v1/README.md). Implementation
remains **24fa36803081e5077d5977baa91441a2c8534ec8**, A handoff publication
7639542cd28552bd7b9c6b65dcf47f256ce81653, and B audit/start HEAD
94b072ef5b78aab9a3c1ff97639ddfb4f65b9e26. Later main integration is recorded separately in
preparation-receipt.json. No production or historical files change.

The concrete approval is in [decision.md](decision.md); [procedure.md](procedure.md)
contains the guarded installation/publication/run sequence. [validation.md](validation.md)
covers all **133 cases × 3 repetitions × 2 modes = 798 public calls**, 780 expected successes
and 18 TimeOverflow refusals, plus two fresh-layout saved-result replays with discriminating
fault/restoration checks. All those public calls remain **unexecuted**. This does not install
HostRecord/HostSelector authority or lift U0024, C3, performance or qualification boundaries.

## Exact deployment inputs

| Input | Identity / binding |
| --- | --- |
| Existing image | `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523` |
| Debug executable | `sha256:7ed3bad6b96ceb3cf7dfc2d31e69d88b7efbadcccef47810a80728b4a11c6cd5` |
| Release executable | `sha256:ccbbe96853f03e591234885099d47ccea6487787c6061c66777c76f71f1436b4` |
| Existing Python 3.12.14 executable | `sha256:f7c6210eb40fadcd3c2889dddd24a15fc2c9f926aec5a03bf9da66e12d581526` |
| Existing Python distribution inventory, 4532 members | `sha256:b5989e367b873cbcfcb64c0e40ac889f4fadf4ed96cc98b686c4252a26d8749a` |
| Existing selected Python packages inventory, 152 members | `sha256:98522510fa25cca5267e1ab5845667057f40b487209d0614a9c333c14dea049b` |
| Candidate deployment closure | [candidate-layout.json](candidate-layout.json), 372 exact files, 300305411 bytes; includes actual binaries, source, read/build receipts, corpus and saved jobs |
| Frozen case/clock/profile/registry/job joins and seven-field decision subject | [campaign-plan.json](campaign-plan.json), unchanged candidate-04 inputs |
| Future container helper identities | [campaign-files.expected.json](campaign-files.expected.json); only five files mounted in /campaign |

Pydantic 2.13.5, pydantic_core 2.46.5, annotated_types 0.8.0, typing_extensions 4.16.0 and
typing_inspection 0.4.4 are the **already available host tools**, copied by exact inventory.
Their installed metadata/licences remain in the selected files. No editable project, .pth
activation, pytest or optional package is installed into the image. Existing unused Tcl/Tk
files remain part of the frozen Python distribution; GUI imports are forbidden and no
optional system dependency is proposed. This is local use, not redistribution.

The Python resolver imports only /candidate/{src,contract} and the exact B literal checker;
the native process executes the resolver's retained verified ELF descriptor directly.
Docker launches Python's environment, **not a replacement executable presented to the resolver**.
No generator/oracle is invoked. The 372-file runtime closure and 4532/152 tool inventories
are not the generator support inventory. Its observed 56 entries remain unchanged, not a quota.

## Evidence and limits

New: read/hash of all selected files; exact finite membership checks; static ELF/library
inspection inside the existing image with UID1000, no capabilities/network, read-only inputs;
private regeneration of both tool inventories; host-only proposal guard tests and lint.
The interpreter/Pydantic needed-library names and required symbol versions are present.
The raw static command receipt and compact observations are published; bulk inventories are
reconstructible with inventory_runtime.py and remain private. The ld.so.cache binding is
inherited from the completed audit; other listed library hashes were rechecked here.
No mounted Python/native payload, authority resolution or mapped execution was performed.

Inherited, not rerun: both exact candidate builds, bounded read audit, three DTO families,
45 native units/mode, 48 DTO cases/mode, 133 admissions/mode, 11 invalid public controls/mode,
224 host/process/loader tests, 16 isolation/currentness controls and schema export. The prior
266 public tests were only collected. None supplies a successful public mapped result.
Static symbol availability is not dynamic ABI proof; the proposed preflight is the narrow
remaining runtime check. If it fails, preserve evidence and return the concrete missing
library/import/security requirement; no automatic dependency or security fallback.

No extra compatibility review is requested. The remaining decision is the exact deployment,
genuine subject binding and finite first-use execution scope described in decision.md.
