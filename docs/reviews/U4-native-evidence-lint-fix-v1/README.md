# Historical native evidence lint correction

The tracked export at `f7eda287ddfd9d0c5bae96e3e5b24552becd6710` reproduces 145 Ruff errors in six archived execution recipes from U4-A-component-native-v1. These files are hash-bound historical evidence with scratch-specific paths, not maintained application or test tools.

An evidence-local `ruff.toml` inherits the root configuration and excludes only those six exact paths. No lint rule, root configuration, active source, workflow, receipt or historical manifest changed. All six recipe bytes remain unchanged and match their original manifest hashes.

A clean tracked-export `ruff check .` passes. Comparing complete file lists proves exactly those six files leave lint scope; only the new configuration itself enters it. [Checks](checks.json) records identities and file counts, including correction of the initial scope assertion. This classifies archived evidence explicitly; it does not claim those scripts became lint-clean.

No recipes were executed. No native builds/tests, full Python suite or hosted CI monitoring ran. Issue-edge Stage 2 proposal and review pins remain unchanged. Future maintained executable recipes should meet root lint rules; immutable transcripts can use the existing `.py.txt` convention.
