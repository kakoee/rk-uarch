# Fresh published-source verification

Author-run U0024 verification; independent review and remote qualification remain pending.
The published proposal was fetched in a new clone from `origin/main`, reconstructed into a
new disposable source directory, and checked locally. Protected files remained unapplied
in the coordinator and published main.

The first published reconstruction exposed three line-length failures after the final
admission-variable rename and timing-harness edit. They were corrected by formatting and
shortening a timing-description string. No service, mapper or observation law changed.
The initial negative fixture was also strengthened to keep unrelated buffer references
valid and assert the exact mandatory-accumulator-traffic refusal. Its focused rerun passed.
These findings were corrected, not treated as deferred infrastructure failures.

The fresh reconstructed native source passed debug and release builds, 86 unit tests and
2 ordinary-process tests, fmt and clippy. The native source stayed byte-identical through
the later Python fixture/formatting corrections. The fresh small Python regression passed
60 tests with 2 explicitly deselected large gather fixtures in 5.63 seconds. Their completed
focused evidence and the completed all-52 campaign were reused without restarting cases.
The final source proposal is commit `4ce1a0aab0c9435a4158a4e3d1d96147bb3dd7f6`, reconstructing tree
`8739acc691ee2a81efcf14a035f28dd897024e0d`. It was fetched from origin in the new clone and exported again into a fresh
source directory. That exact reconstruction passed the small suite again (60 passed,
2 deliberately deselected in 4.57 seconds), both mypy commands, Ruff, import boundaries,
original/reference/native schema checks, debug/release builds, 86 native unit tests and
2 process tests, fmt and clippy. `evidence/published-*.txt` records those final checks.
Large gather evidence, licences/vendor checks and the completed campaign are reused
with their stated scope. Subsequent receipt-only commits do not change this source tree.

This checks the source proposal, not an installed protected transition. No remote job was
polled or called passed, and this author receipt is not an independent review signature.
