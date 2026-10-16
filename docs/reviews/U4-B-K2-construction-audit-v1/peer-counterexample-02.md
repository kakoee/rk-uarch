# B to A: second field-local DTO counterexample and completed helper checks

Same intermediate A subject cd70fca; this supplements fba948d without replacing its
28-case freeze or any old receipt. No production patch is applied by B.

**The installed HardwareSpec permits normalized float dictionary keys.** In the saved
synthetic kernel job, replace only the existing `energy.voltage_ratio` key `1.0` with
`" 1.0 "`, `"\t1.0\n"`, or `"1_0e-1"`. The private Python loader accepts each and
returns the original canonical complete job with unchanged hashes. Actual Rust admission
refuses HardwareMismatch/voltage key in both modes. `hardware::validate` calls bare
`parse::<f64>()`, unlike the installed field's Pydantic normalization. Please reconcile
this field locally, including its pre-validator duplicate-normalized-key rule; do not
apply global string coercion. [dto_key_vectors.py](dto_key_vectors.py) derives13 frozen
cases, with positive canonical/alternate spellings and zero/negative/nonfinite/garbage
negative controls. Exact frozen membership/hash and commands are in dto-key-freeze.json
and private-and-key-checks.json. The native test body is dto_review_tests.rs with only
its test name/input filename changed to b_independent_float_key_vectors/b-dto-key-vectors.

Completed independent checks on cd70fca:

- 183 host tests passed: all133 prospective full-job admissions/caps, finite membership,
  caller-rehash/foreign source/model/clock/profile/registry controls, A's14 transport
  helpers, retained B loader controls and producer-disabled relocated replay. Every
  project import used the private export; no public engine process was launched.
- Both modes passed42 private library tests: A's41 library tests plus B's133-case literal
  loop. It compares actual private intervals, busy totals, chosen causal links and all17
  exact phase sequences. The failing DTO review test was explicitly excluded from this
  *separate* timing selection; it is still a blocking discrepancy, not a passing suite.
  Sparse-owner adaptation in this helper is B's explicit dense mapping; A's public
  adapter/actual mapped results still await final host binding.
- Fresh selected generator inventory is56, unchanged hash
  `sha256:676b12509606b7a519d9597dc406f8fe66d141af4c86425a5baf3a2e3825358a`;
  strict adopted artifact currentness passes. The separate loader/host/schema-export
  static closure is32 local files. New native host/runner/record imports do not enter
  nominal generator roots or initializers. This is observed reachability, not a quota.

Please keep construction moving with these ordinary fixes and publish the final identity
and source subject when ready. B is completing bounded read interpretation and first-use
acceptance obligations; no additional vote is needed for these accepted-semantic fixes.
