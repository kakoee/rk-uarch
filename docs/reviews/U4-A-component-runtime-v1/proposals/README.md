# Unapplied proposal selection

Use **D3-v3-unapplied.patch** and component_negative-v3.py.txt. The patch creates
src/rkuarch/engines/native/component_negative.py only in a fresh private export; the
live tree has no such module. All earlier proposal bytes remain present.

Version1 reused the K2 decoder and cannot consume the complete component refusal set.
Version2 selected the new decoder but omitted its import; its actual helper invocation
failed with NameError. Neither is a passing final proposal. Version3 adds the explicit
component decoder import; six private proposal controls and all40 actual final native
unit refusal envelopes/profile joins pass. Native zero-entry evidence is separate and
is not inferred from those envelopes. These are private/unapplied checks, not public D3.

B-consumer-types.patch is separately unapplied and owned by B. It adds only an int
argument/return annotation to runtime_checks.population. A cold strict typecheck passes
in its private patched export. A did not edit the live checker or silently change B's
consumer binding; actual B installation/pin transition and final joined review are due.
