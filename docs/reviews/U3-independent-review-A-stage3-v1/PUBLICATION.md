# Coordinator publication note

Original reviewer reports, logs, receipts, scripts and checks are unchanged.
Immutable probe source is published verbatim as `*.py.txt` rather than maintained Python
modules. Before replay, use a private copy/export and copy each `name.py.txt` to `name.py`
in this directory, then inspect and run the original recorded commands with their pinned
revision, environment and explicit import origins. Do not replay fault probes on live code.
The source bytes and original relative paths are recorded in
`docs/reviews/U3-closeout-documents-v1/evidence-publication.json`.

This packaging is coordinator work, not a new reviewer verdict or a change to results.
It introduces no lint exemption and does not rewrite evidence to satisfy style checks.
Original local `.py` files remain preserved/uncommitted; interpreter caches are not selected
for publication. Generated workload/checkpoint trees are not part of this evidence.
