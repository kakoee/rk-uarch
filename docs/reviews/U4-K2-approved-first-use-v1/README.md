# Approved conditional first-use sequence

Javid approved U4-K2-deployment-and-first-use-v1 with "yes". See
[acceptance.json](acceptance.json), binding the unchanged B package at
`f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f` and coordinator decision `438e34b`.
The approval covers the ordered deployment/preflight/publication/installation/campaign
sequence; it does not assert that an unexecuted preflight passed.

The exact package is exported at `/tmp/u4-k2-approved-preparation`, the two inventories
at `/tmp/u4-k2-approved-inventories` and the new payload at
`/tmp/u4-k2-approved-payload`. [preparation.json](preparation.json) records the read-only
checks: 4016 regular files, 1048 confined symlinks, 406378508 bytes. No source/runtime,
first-use authority, selector or mapped job was installed/executed.

[human-stage.py](human-stage.py) wraps only step 2 of B's approved procedure. Default
is read-only checks; --place requires its actual published helper commit and invokes the
human sudo copy/seal of the fixed new root. It independently checks exact payload membership,
bytes, confined symlinks, absence of authority, destination ancestors and nested mounts.
It will not overwrite an existing deployment. A partial failure is retained, not deleted
or retried over existing files. The root command never changes existing parent permissions,
host libraries, host Python or host /etc/rkuarch. Do not run the Python interpreter as root.

After the human returns the verified placement receipt, the coordinator runs the already
approved authority-free mounted-runtime preflight. Only its actual success permits recording
the exact first-use decision/HostRecord and publishing the genuine preflight. Human authority
placement and all 798 public calls/replays then follow the same existing approval; no new
semantic vote is needed between stages. Any failed prerequisite stops dependent execution.

The original B package/helpers are unchanged. No runtime, native or construction suites were
repeated here. Root placement, container preflight and public calls remain unexecuted.
