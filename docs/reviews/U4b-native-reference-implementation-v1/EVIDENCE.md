# Local implementation evidence

Author-run, interim local evidence under U0024. This is not independent review, a hosted
CI result, device evidence, a performance qualification or U4 closure. The complete source
is the reconstruction recorded by `source-tree.txt`; publishing this package does not
install its protected changes.

## Executed checks

| Check | Actual result | Evidence |
| --- | --- | --- |
| Reference arithmetic/process/fault tests plus existing ordinary `/4` unit/process tests | 62 passed; no skips | `evidence/python-integration.txt` |
| Native unit/property tests and ordinary process tests | 86 unit tests and 2 process tests passed; no ignored tests | `evidence/native-tests.txt` |
| Native fmt and clippy (`--all-targets`, warnings denied) | Passed | `evidence/native-fmt.txt`, `evidence/native-clippy.txt` |
| Whole-repository Ruff | Passed | `evidence/ruff.txt` |
| Both repository mypy commands | Passed, 109 source files and 39 contract-test files | `evidence/mypy.txt`, `evidence/mypy-contract-tests.txt` |
| Import boundaries | 2 kept, 0 broken | `evidence/imports.txt` |
| Existing and additive schema checks; native reference schema export | Fresh | `evidence/schema.txt`, `evidence/reference-schema.txt`, `evidence/reference-native-schema.txt` |
| Committed vendor snapshot | Manifest, matrix and compatibility verified | `evidence/vendor.txt` |
| Third-party licence and patch checks | 3 tests passed; reverse/forward chain verified | `evidence/licences.txt`, `evidence/third-party-patches.txt` |
| Preserved peer report-test correction | 2 affected tests passed | `evidence/peer-report.txt` |
| Noneditable installed CLI run and replay, outside the source tree | Passed with an ordinarily copied native executable | `evidence/installed-use.json` |
| Approved all-52 campaign | In progress; completed cases are preserved | Final receipt will be attached after the running campaign completes |
| Exact published proposal reconstruction/recheck | Pending fresh published-source reconstruction | Final receipt follows |

The zero-test Rust binary/doc-test targets are not counted as passes. No CI status was
polled. No dependency, golden expectation or vendor content was regenerated. Unchanged
Cargo/Python locks and the existing accepted dependency licence baseline are reused;
`cargo-deny` was not installed or rerun. The normal Python licence/patch checks above were
executed. Historical exhaustive campaigns, remote/native nightly and controlled-host
performance campaigns were not repeated or called passed.

## Commands and environment

Python tools: existing CPython 3.12.14 environment, with `PYTHONPATH=contract:src` in the
private implementation/reconstruction for source checks:

```sh
pytest -q tests/reference tests/unit/test_ordinary_native.py tests/native/test_ordinary_process.py
ruff check .
mypy src contract/uarch_contract scripts
mypy --no-explicit-package-bases contract/tests
lint-imports
python -m uarch_contract.generate --check
python -m uarch_contract.generate_reference --check
python native/export_reference_carriers.py --check
python scripts/vendor_rk.py --check
pytest -q tests/unit/test_third_party.py
python .github/check_third_party_patches.py
```

The process suite was supplied explicit `REFERENCE_NATIVE` and `ORDINARY_NATIVE` paths to
the actual debug executable; none of those native tests were silently skipped. Rust checks
used the existing accepted Rust 1.99.0 image and offline cache, unchanged lock and Linux
target, with ordinary Cargo commands: `fmt --all --check`, `clippy --locked --offline
--all-targets --target x86_64-unknown-linux-gnu -- -D warnings`, `test --locked --offline
--all-features --target x86_64-unknown-linux-gnu`, and debug/release builds.
The existing image is
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
It was already present, with networking disabled; no image pull, package download or host
privilege change occurred. This records test context, not a build-attestation requirement.

The host is local x86_64 WSL2 Linux, kernel
`6.6.87.2-microsoft-standard-WSL2`. Compiler and installed dependency versions are in
`evidence/compiler.txt` and `evidence/dependencies.json`. The wheel was built offline,
installed noneditably with `uv pip install --offline --no-deps`, and run from `/tmp` outside
the checkout. Its temporary environment reused the existing installed dependency directory
through a normal `.pth` path; nested editable project startup files are not processed by
that path addition. The actual `rkuarch` and `uarch_contract` origins are the wheel's own
site-packages, recorded in `installed-use.json`, not the coordinator source tree. Reference
schemas and nominal values were confirmed present in the wheel. An offline dependency
resolution attempt lacked cached registry records; no downloads were made to resolve it.

The integration command uses explicit suite/coefficient paths and ordinary executable
choices; there is no authority or executable-digest argument:

```sh
python validation/reference/run_integration.py \
  --suite validation/L3_silicon/tpu-v5e/u4b/suite-proposed.json \
  --coefficients validation/L3_silicon/tpu-v5e/u4b/inputs/rotary-coefficients.json.gz \
  --debug /path/to/debug/uarch-engine --release /path/to/release/uarch-engine \
  --python /path/to/noneditable-environment/bin/python --output /tmp/u4b-campaign
```

Supply absolute input paths when running from a different directory. It prepares each
saved job once; all execution is native. Every selected job gets three fresh release
processes and one debug process, byte-equal complete results, installed saved replay with
mapper/preparation imports disabled, and native execution with two primes. The second
result has its own content identity and input bindings verified; exact normalized equality
of all remaining result content reuses the first result's schema and independent-law checks.
Only the legitimate input identities, result self-hash and priming count are excluded from
that comparison. Metadata, context, counts, critical causes and every activity must match.
The receipt reports sizes/hashes and pass scope, not a nominal prediction-duration table.
Retained C0 comparisons are recorded without treating their additive compute formula as a
universal overlap bound; the separate native resource-demand law is asserted by the checker.

## Independent expectations and discrimination

The tests encode arithmetic independently of mapper/native calculated answers:

- BF16 3×130×7: 5,460 useful matrix ops; reads 2,600 B, final output 42 B, explicit
  VMEM traffic 2,978 B including 336 B of partial traffic; one final 21-element cast.
  Raw INT8 has INT32 output and no BF16 conversion. The 3×5×7 analytic example has 210
  matrix operations, 21 casts and 142 mathematical operand bytes.
- RMSNorm 2×4: 26 multiplies, 6 reduction combines, 2 epsilon adds, 2 rsqrt and 20 casts.
  Residual/SiLU work has separate literal expectations. Four BF16 read elements require
  8 input bytes, 4 widen casts, 3 combines and a 4-byte output. Length one has no combine
  stage or reduction-multiplier read.
- Small Q/K RoPE: 36 arithmetic operations and 24 casts, versus 12,288 issued arithmetic
  lanes and 4,096 issued casts. Q/K coefficient traffic remains 32 B, with input/output
  traffic separate; position-zero coefficients do not erase declared work.
- 2049-token K+V gather: 8,392,704 valid payload bytes, plus 516/260 index bytes at page
  sizes 16/32, with complete contiguous output. Both are correctness fixtures, not new
  suite rows. Rehashed wrong-page transfers refuse in Python and native admission.
- Small decode GQA and triangular prefill each have 96 useful QK+AV operations and 60
  conventional semantic softmax operations; issued dense/padded work stays distinct.
- Synthetic startup/control/latency/rates produce literal total durations of 42 ps
  (window 2), 52 ps (window 1), and 41 ps (fractional 3 B/ps service). The fractional
  cursor expectation is 67/3 ps. These synthetic numbers are not TPU predictions.
- An explicit spill adds 84 B HBM read, 84 B HBM write and 168 B VMEM endpoint traffic,
  retaining 5,460 matrix operations and not shortening execution. Halving the BF16 MXU
  rate lengthens service without changing counts. Imported insufficient accumulator
  capacity refuses instead of triggering hidden retile.

Controls mutate identities, coverage, duplicate tails, precision, units, capacities,
preloaded VMEM, final stores/casts, omitted mandatory partial traffic with dependency order preserved, producer edges, fractional outstanding counts,
unearned factual provenance, coefficient bits, page addresses, activity service/count/
owner/inventory, credit data, allocation intervals, state and critical causes. They must
refuse rather than return success. CLI/request protocol mismatches refuse. The unmutated
baseline and saved replay pass around these controls. Native admission independently
checks the source, not merely a Python-supplied count or duration assertion.

Development checks found and fixed an unordered K/V scratch reuse, implicit packed-to-
contiguous joins, missing coefficient bit-string schema support, a component wire-limit
regression, and incorrect zero-stage reduction read reporting. Final focused tests include
their controls. Earlier all-suite receipts for unaffected units are reused for the last
zero-stage checker correction: those units have no zero-stage reductions, and their stricter
prior count comparison already passed. The final 62-test consolidated run exercises the
corrected checker and both admission paths' mandatory accumulator-traffic law. The all-52
campaign retains its original native binary; that last admission-only tightening does not
change successful service, mapping or observations. Its rehashed omission fault and ordinary
positive/spill cases pass against the final binary. Exact supplied page-index bytes are
used by gather preparation; their unchanged values are recorded in baseline-preservation.json.
The omission fixture was further tightened to preserve unrelated buffer references and
assert the specific mandatory-traffic refusal at both boundaries; its final focused rerun
passed (`evidence/partial-control.txt`). No completed campaign case was restarted. Observational timing was added to subsequent
workers during the layer-b8 case at the user's request; it changes no checking law. No hardware parameter was tuned to make a check pass.

## Remaining human and external work

Protected installation and independent review remain outstanding. Human L1 GEMM/DMA
worksheets are not supplied or signed by this author. The source-level suite still requires
compiler/event/mapping/state correspondence and both lane signatures before final benchmark
acceptance and any U5 freeze. U-P9 owns ordering/frozen predictions; U-P10 owns measurement.
Remote/controlled-host obligations stay as stated in U0024/U0023. No device access, spending,
silicon measurement, frozen predictions, final benchmark acceptance or U4 closure occurred here.
