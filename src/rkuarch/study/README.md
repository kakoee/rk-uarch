# study — comparing designs

A StudySpec names a base design, the parameters to vary, a versioned workload suite (or one
request template), one engine and fidelity. Variants may change only what a proposed design
is free to choose: stipulated values (counts included), categorical fields, and the mapping
policy; each change is recorded in conditional_on. A reference is never varied.
Tables are cached by request hash. The diff report shows which regime moved and why, per
workload and as a geometric mean of normalised speedup (never an arithmetic mean of ratios), a
one-at-a-time tornado labelled "local sensitivity at these points, not a ranking", energy with
its own conditions (unverified until its rung exists), and each variant's detail delta against
its own U-C0. No optimiser, no fitted surrogate, no area model.
