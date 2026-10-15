# Human source receipt and next input-staging preparation

The human source commit is verified locally in the existing A clone:

- Commit `0cf24d91eeca5cc45182eb6fb03202677fd97dcb`.
- Tree `275bcefbe616a049aa6d0a968ff81b5728f0563d`.
- Parent `8c9ee91be4f8f0e46f8af8f8684053fca30d9111`.
- Exact 32 approved paths/postimages; clean tracked/index/untracked state.
- All 56 selected support paths/digests match B's audited closure.
- Complete vendor script: `b82ae570dee99466389d609051425c501022d1ebf03a2bc67a27a27c1b76`.
- Embedded oracle unchanged: `bca579505e96e3f105d4442e7b6c52c3cbe87316edde3ea896692abceb90993b`.

The pasted receipt's formatted scripts initializer was checked against the actual Git path
`scripts/__init__.py`; there is no path discrepancy in the real commit. No source commit was
pushed, adopted artifact edited, K1 reviewed or remote infrastructure contacted here.

[Next decision](next-decision.md) requests only human input staging and verification.
[The helper](human-stage.py) pins [source/environment/output identities](source.json).
It prepares no inputs in check-only mode. Its staging branch is unexecuted; input digest,
freeze acceptance and actual generation/adoption remain pending. The future generator helper
will bind the returned real input digest and separately checked oracle environment/upstream.
The old adopted artifact remains unchanged and stale against S; this is not a currentness pass.

The existing coordinator interpreter is used only for pure input preparation. Recorded
NumPy is 2.5.3 in this environment; that is not a claim about the separately locked rk-sim
oracle environment used in earlier generations. Do not substitute staging package metadata
for the future generator's actual environment receipt.

Prior 39 preparation / 173 admission-policy test results and B's broader results remain
inherited through exact source postimage verification, not freshly rerun suites. This package
adds ordinary review tooling only. Syntax/static/preflight checks are recorded separately
once the helper is pinned; no source-wide manifest, checkpoint copy or guessed input digest.

A's author must keep the installed source unchanged while this lifecycle runs. The independent
K1 reviewer can continue against its own pinned published export. Generation/adoption, K2,
source publication and infrastructure remain separate from the staging decision.
