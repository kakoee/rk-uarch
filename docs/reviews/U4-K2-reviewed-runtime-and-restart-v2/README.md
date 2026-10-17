# Combined K2 runtime — scoped acceptance and next decision

The same independent reviewer ACCEPTED all six Stage 2 response rows at
`e2649edf3ad99816d7879d7dc81e2646e4a09975`, helper
`0c4afcfa0ab314724afa869ac2d5736a22fb0e89`, candidate SHA256
`ecc0dfafea975701bd933beda08735d0def9c7a3e76c03616a543a98664c9b81`.
This records the reviewer's software-response verdict; it does not grant human policy,
installation, runtime authority, campaign completion, qualification or U4 closure.

Coordinator verified the 18,864-byte Stage 1 prefix, all earlier pinned review inputs
(including the restored pending stress receipt), all 21 declared package identities, helper
ancestry, and both protected patches' exact pre/postimages in a disposable directory.
[Checks](checks.json) distinguish this from the reviewer's runtime and fault tests, which
were not repeated. The proposed v2 runtime root remains absent.

## Review preservation

[review-evidence.tar.gz](review-evidence.tar.gz) preserves 26 exact report/probe/receipt files
(about 32 KB compressed), with original repository-relative paths. The archive excludes
runtime trees, caches and raw scratch logs. [Manifest](review-manifest.json) gives every
file's size/hash and the archive digest. A readback verified every archived byte.

The full report is 29,534 bytes, SHA256
`583062b7f65064c53bf93f63782427239be677c4a1d9b7dddd14928a062d70d6`.
Its original 18,864-byte prefix remains
`6949858ea0d24392497c93ca93d726e42af466b0ef015b00c972538b85208ff2`.
The reviewer restored the exact pinned Stage 1 polling receipt after disclosing its earlier
in-place update; the completed stress run is a separate Stage 3 record and does not support
F4's adjudication. Original live review files remain untouched and unstaged.

For a fresh checkout, unpack the archive into a NEW private directory and open
`docs/reviews/U4-K2-combined-runtime-independent-review-v1/README.md` there; its relative
probe/result links resolve inside that directory. Do not extract over the original evidence
or execute archived probes as part of normal CI. Archiving preserves executed source bytes,
including their original formatting, without silently rewriting reviewer scripts.

## Observation triage — no new runtime corrections required for this decision

| Observation | Disposition and next boundary |
| --- | --- |
| O-S3-1, indirect F4 test failure | Non-blocking regression maintenance. At the next change to B's launcher tests, limit the Popen fixture to the first launch so the kill-path symptom is asserted directly. Preserve the existing deterministic reproduction and reviewer acceptance. |
| O-S3-2, real-private F3 regression | Non-blocking regression maintenance. Before the next packaging-test revision is relied on, promote the reviewer's real-private-receipt attack into a durable regression that fails on acceptance, not KeyError. Its exact probe/revert are preserved now. No change to accepted runtime bytes is needed. |
| O-S3-3, mount-source layout assumption | Mandatory real-placement preflight check. Verify the actual Docker-host mount sources against the unchanged accepted check. If they differ, stop for reconciliation; no override, fabricated seal or substitution of private receipts. Reviewer's observation that this host fits is inherited, not a new coordinator mount test. |
| O-S3-4, main changes during remote verification | Expected safe operational refusal. Keep actual-remote checks intact. A preparation-only render may be repeated with the same pinned subject after a transient remote race, preserving failed diagnostics; this does not authorize repeating a campaign, replay or partially completed placement. An execution-stage refusal follows stop-on-failure. |

B owns the two maintenance items. They are recorded follow-ups, not another required author/
review cycle before the unchanged accepted candidate can be considered. The existing component
A/B assignments and independent review remain separate.

## Next

Present [the exact combined decision](next-decision.md) to Javid. After genuine approval,
record it verbatim, prepare the human protected-documentation and immutable-payload steps,
then inspect actual preflight before binding any runtime selector. The approved sequence may
then proceed without repeated policy votes, with human-only actions performed by Javid.
Existing accepted installation/authority mechanisms remain mandatory.

Both this runtime and the component proposal amend U0011. Preserve both intended decisions
when sequencing later installation; component postimages must be reconciled against the then
installed ADR. Do not overwrite one proposal with the other's older full-file postimage.
