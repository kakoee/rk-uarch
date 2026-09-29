# L3 silicon — predictions first, then measurements

Per reference chip: SUITE.md (signed by both lanes before predictions exist), predictions/
(committed in one "FROZEN PREDICTIONS:" commit, never edited), UNKNOWNS.md (every stub the
engine read), results/ (raw and immutable). check_ordering.py fails CI if any result appears in
a commit at or before its prediction's. A new prediction is a new file in a new commit.
