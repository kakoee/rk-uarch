# rk-uarch

A microarchitecture-level simulator of one AI accelerator. It turns a hardware spec and an
LLM model description into a characterization table — the cost of one inference iteration
per (batch, context) point — at a stated fidelity, with its own errors measured and a badge
earned only against real silicon. rk-sim reads those tables to price a custom ASIC at C2.

## Quickstart
    uv sync --extra dev
    make test-fast
    uv run uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine analytic
    uv run uarch report tables/<hash>.json

## Repo map
contract/ the shared vocabulary · hw/ designs and references · src/rkuarch/ the harness ·
native/ the Rust engine · validation/ the evidence · measure/ silicon kits · docs/ everything else

## Working here
Read CLAUDE.md, then docs/build-spec.md §0. Sprints and prompts: docs/execution-plan.md.

## Status
See docs/execution-plan.md STATUS and docs/how-it-works.md.
