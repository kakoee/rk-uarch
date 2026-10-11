# Produce a U2 table and report

Run from the repository root after `uv sync --extra dev`. This example estimates
Llama-3.1-8B on the stipulated H1 (`npu-l4`) design, BF16, tp=1, at nominal frequency.
The eight points are decode batch 1/8 × context 128/512 and prefill prompt count 1/4 ×
length 128/512. A decode row is one iteration generating one token per active sequence;
a prefill row processes its stated prompts. Neither includes inter-chip collectives.

## Prepare and draft

Use a fresh output directory. `tables/` is ignored by Git.

```sh
mkdir -p tables/u2-example
cat > tables/u2-example/grid.json <<'JSON'
{"decode":{"batch":[1,8],"context_per_seq":[128,512]},"prefill":{"n":[1,4],"L":[128,512]},"frequency_ratio":[1.0]}
JSON
uv run uarch validate hw/designs/npu-l4.yaml
uv run uarch assumptions --model physical-resolved --output tables/u2-example/assumptions.json
uv run uarch prepare hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --tp 1 \
  --grid tables/u2-example/grid.json --output tables/u2-example/prepared.json
uv run uarch capture --prepared-input tables/u2-example/prepared.json \
  --assumptions tables/u2-example/assumptions.json --output tables/u2-example/capture
uv run uarch companions draft --prepared-input tables/u2-example/prepared.json \
  --assumptions tables/u2-example/assumptions.json --capture-dir tables/u2-example/capture \
  --output tables/u2-example/draft
```

**Stop for independent review.** The draft is UNREVIEWED. Supply all inputs, capture
members, source declarations and comparison attempts to an independent reviewer.
The final declarations and explicit hardware-family registry need actual accepted
`ReviewRecord`s for their exact `review_subject_hash` values. A registry proposal must
state its basis; a name alone does not establish a relationship to measured hardware.
No command invents review authority. Code-review approval does not supply these records.

The reviewer must check intake completeness. This fresh standalone example makes no
comparisons. That is distinct from U2's earlier full-matrix attempts; it cannot replace
their ledger or close their gates. If comparisons belong to your run, retain **every**
attempt, including failures/refusals and original source closure, and review the final
comparison recipes. Never use the empty-intake option to hide earlier attempts.
See [the detailed carrier and intake rules](../src/rkuarch/table/companions.md).

## Assemble after review

The following commands require actual accepted `recipe-review.json`, `registry.json`
and `registry-review.json` in `tables/u2-example/`. They are not produced by the draft
command. The completed example using actual independent declaration reviews is recorded in
[U2-public-demo-v1](reviews/U2-public-demo-v1/completion/README.md). Those reviews bind
only its exact subjects; they cannot be reused for changed declarations.

```sh
uv run uarch companions assemble --prepared-input tables/u2-example/prepared.json \
  --assumptions tables/u2-example/assumptions.json --capture-dir tables/u2-example/capture \
  --recipes tables/u2-example/draft/metric-dependencies.json \
  --recipe-review tables/u2-example/recipe-review.json --registry tables/u2-example/registry.json \
  --registry-review tables/u2-example/registry-review.json \
  --model-card tables/u2-example/draft/model-card.json --no-comparisons \
  --artifact-dir tables/u2-example/companions --output tables/u2-example/context.json
uv run uarch table --prepared-input tables/u2-example/prepared.json \
  --assumptions tables/u2-example/assumptions.json --capture-dir tables/u2-example/capture \
  --context tables/u2-example/context.json --model-card tables/u2-example/draft/model-card.json \
  --artifact-dir tables/u2-example/companions --output tables/u2-example/table/table.json
uv run uarch report tables/u2-example/table/table.json \
  --output tables/u2-example/default.html --markdown tables/u2-example/default.md
uv run uarch report tables/u2-example/table/table.json --show-unvalidated-predictions \
  --output tables/u2-example/optin.html --markdown tables/u2-example/optin.md
```

`--capture-dir` reuses authenticated saved jobs/results without preparing or executing
again. For the fresh execution path, omit `--capture-dir` while keeping the reviewed
prepared input, assumptions and companions. The table package retains its adjacent
`artifacts/` directory for offline reporting. Keep that whole package together.
Use distinct HTML and Markdown destinations for the two modes; conflicting output
bytes refuse instead of silently overwriting.

`make table ARGS='...'` and `make report ARGS='...'` forward the same CLI arguments;
with no arguments they display help. `make typecheck` runs both CI typecheck commands.

Default reports show the stipulation count and readable identities while hiding
unvalidated predictions. Opt-in predictions remain labelled STUB, error unknown and
energy unverified. Verified bytes are not measured performance. Only the analytic
engine and workers=1 are supported for this U2 workflow; later engine and worker
capabilities are not claimed here.
