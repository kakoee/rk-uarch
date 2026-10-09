# U2-source-input-freeze-v2 — proposed

This replaces the current source/input binding for a new RR-C1 artifact revision; the previous accepted freeze and artifact remain historical. Acceptance is pending and recorded separately. The only production change sorts table provenance conditions by path. It changes table identity deterministically; no workload, hardware, threshold or proof policy is changed.

Exact review subjects:

- Implementation/test Git tree: `36f24dc4b0a1a27775f6a566fb913ed3d8cd177e`, based on `7aab97d35ca554b0477ac5719dfa4e5306f8bbab`; source-delta.patch and source-tree.json record the two paths. No new whole-worktree source manifest.
- Input manifest: `9a30b29029a32339dfc6062e138cebc23f7f1474044b414068dd9c8113c1dca0`.
- Previous input manifest: `81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898`.
- Previous adopted MANIFEST: `2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44`.
- Upstream pin: `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.
- Proposed new destination: `docs/reviews/U2-real-generation-v2/candidate` in the integration worktree. It does not yet exist.

Only support-files.json and SHA256SUMS differ among the 24 prepared input files. All 22 other files are unchanged. The support inventory still has 84 entries; only src/rkuarch/table/build.py changes. Seven component/precision pairs, 1,008 workload cases, all hardware/model descriptors and accepted efficiency inputs remain the same. No changed numerical result is presumed acceptable: compare all newly generated counts, durations, nulls and refusal outcomes before adoption.

Read-only preflight passed: exact Git source/test tree, strict revised input bytes/support, previous artifact integrity, clean pinned rk-sim checkout, and unchanged existing external environment. CPython 3.12.14, locked environment `/tmp/rk-sim-u1-jjaffari-1e5706e`, on ElfinKidsLaptop Ubuntu/WSL2. It reads package metadata without oracle workload calculation. This does not establish a simulator-performance host.

Validation: the clean proposed source tree has 1,017 passing tests, two expected old-artifact/current-support failures and zero skips; lint and types pass. Both failures explicitly name the corrected build.py support byte mismatch. Exact complete actual captured-result rebuilds passed at A and independently at the coordinator. See ../U2-RR-C1-integration-v1/README.md. New-artifact full render/repeat/replay and final U2 exits remain pending.

After explicit acceptance, the coordinator records the exact inventory/input identities in `../U2-source-input-freeze-v2-acceptance.json`. Javid then runs the prepared human-only wrapper as a separate step:

```bash
bash /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-source-input-freeze-v2/human-generate.sh
```

Do not run it before acceptance. It verifies the reviewed code/input/environment, requires an absent generation directory, runs the same generator command in two fresh processes, requires `created: 48 files` then `verified-identical: 48 files`, and records strict inspection and semantic differences. Log checks use Python and do not require rg. The wrapper was syntax-checked only; no generation occurred. If a step fails, preserve its evidence and return for reconciliation; do not overwrite or relabel it.

U0002 requires the reviewed freeze, two human runs and separate explicit complete-candidate adoption. This is the existing lifecycle, not a new policy. No generation by agents, artifact adoption, push, publication, cleanup or sprint closure is authorized by this freeze proposal. Local commit approval remains a separate named decision.
