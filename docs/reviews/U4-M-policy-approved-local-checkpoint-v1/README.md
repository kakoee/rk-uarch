# Approved local adoption checkpoint — human commit pending

Javid explicitly approved U4-M-policy-adoption-local-checkpoint-v1. The
[acceptance](acceptance.json) binds the exact ten-path [commit plan](../U4-M-policy-adoption-local-checkpoint-v1/commit-plan.json)
at `60adee9eb57068ec1f43412a1bd307e5c3d61d21`. Expected parent is
`0cf24d91eeca5cc45182eb6fb03202677fd97dcb`, expected tree
`cc1b99e175bb848d4eba3a04e09cc3d580be870d`. Push remains unapproved.

[Human helper](human_commit.py) first verifies its committed package and the actual approval,
exact live branch/parent, normal hooks, empty index and complete ten-path worktree delta,
every approved postimage, placement receipt and strict currentness/adoption authority.
It reconstructs the expected tree with a temporary index and object store outside A.
`--check` stops there and never stages or commits.

The actual human invocation additionally requires UARCH_HUMAN=1. Only after preflight does
it stage those ten paths, verify the exact staged tree, run normal `git commit` hooks with
the approved message, verify parent/tree/message/cleanliness, and write a receipt outside A
at `tables/U4-M-policy-adoption-v1/local-commit.json`. It never bypasses hooks, amends commits,
pushes, generates inputs/artifacts, changes native code or releases K1/K2. If refused or
interrupted, preserve the state and return diagnostics rather than resetting or rerunning.

The four live adoption gates already passed without skips; helper checks do not claim a
new full suite. Publication and integration of A's local ancestry require separate work
following receipt verification. The uncommitted K1 proposal is not part of this checkpoint.

Docker access was rechecked after Javid supplied the Desktop settings screenshot. Both
client and server now respond as 29.8.2, `/usr/bin/docker` points into the Docker Desktop
WSL integration, and the exact accepted image exists locally as linux/amd64:
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
This supersedes the earlier transient unavailable observation. No Docker setting, tool,
image, container, registry or server was changed, installed, pulled or run by this check.
B and the reviewer can recheck current access for their pending native work; availability
alone is not a new native-test result or remote-CI qualification.
