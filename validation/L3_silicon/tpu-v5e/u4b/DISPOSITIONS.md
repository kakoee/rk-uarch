# Disposition of all 70 historical candidates

The historical `../suite.json` is unchanged. Targets refer to `suite-proposed.json`.
IDs -04 keep a candidate lineage but the **revision-2 shape is changed**; do not join revisions by ID alone.

| Historical candidate | Disposition | Selected unit(s) | Reason |
| --- | --- | --- | --- |
| matrix-bf16-01 | retain | matrix-bf16-01 | Required class and distinct selected work/shape. |
| matrix-bf16-02 | retain | matrix-bf16-02 | Required class and distinct selected work/shape. |
| matrix-bf16-03 | retain | matrix-bf16-03 | Required class and distinct selected work/shape. |
| matrix-bf16-04 | replace_shape | matrix-bf16-04 | Replace redundant full/low 256-cube with 1024-cube to cover full/middle intensity, particularly the missing BF16 middle bin. |
| matrix-bf16-05 | retain | matrix-bf16-05 | Required class and distinct selected work/shape. |
| matrix-bf16-06 | retain | matrix-bf16-06 | Required class and distinct selected work/shape. |
| matrix-int8-01 | retain | matrix-int8-01 | Required class and distinct selected work/shape. |
| matrix-int8-02 | retain | matrix-int8-02 | Required class and distinct selected work/shape. |
| matrix-int8-03 | retain | matrix-int8-03 | Required class and distinct selected work/shape. |
| matrix-int8-04 | replace_shape | matrix-int8-04 | Replace redundant full/low 256-cube with 1024-cube to cover full/middle intensity, particularly the missing BF16 middle bin. |
| matrix-int8-05 | retain | matrix-int8-05 | Required class and distinct selected work/shape. |
| matrix-int8-06 | retain | matrix-int8-06 | Required class and distinct selected work/shape. |
| memory-read-1048576 | retain | memory-read-1048576 | Required class and distinct selected work/shape. |
| memory-read-16777216 | retain | memory-read-16777216 | Required class and distinct selected work/shape. |
| memory-read-268435456 | retain | memory-read-268435456 | Required class and distinct selected work/shape. |
| memory-write-1048576 | retain | memory-write-1048576 | Required class and distinct selected work/shape. |
| memory-write-16777216 | retain | memory-write-16777216 | Required class and distinct selected work/shape. |
| memory-write-268435456 | retain | memory-write-268435456 | Required class and distinct selected work/shape. |
| memory-copy-1048576 | retain | memory-copy-1048576 | Required class and distinct selected work/shape. |
| memory-copy-16777216 | retain | memory-copy-16777216 | Required class and distinct selected work/shape. |
| memory-copy-268435456 | retain | memory-copy-268435456 | Required class and distinct selected work/shape. |
| operator-q_projection-decode | retain | operator-q_projection-decode | Required class and distinct selected work/shape. |
| operator-k_projection-decode | retain | operator-k_projection-decode | Required class and distinct selected work/shape. |
| operator-v_projection-decode | retain | operator-v_projection-decode | Required class and distinct selected work/shape. |
| operator-qk_score-decode | merge | operator-attention_fused-decode | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-softmax-decode | merge | operator-attention_fused-decode | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-av_application-decode | merge | operator-attention_fused-decode | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-output_projection-decode | retain | operator-output_projection-decode | Required class and distinct selected work/shape. |
| operator-normalization-decode | retain | operator-normalization-decode | Required class and distinct selected work/shape. |
| operator-residual_addition-decode | retain | operator-residual_addition-decode | Required class and distinct selected work/shape. |
| operator-ffn_up-decode | retain | operator-ffn_up-decode | Required class and distinct selected work/shape. |
| operator-ffn_gate-decode | retain | operator-ffn_gate-decode | Required class and distinct selected work/shape. |
| operator-ffn_down-decode | retain | operator-ffn_down-decode | Required class and distinct selected work/shape. |
| operator-activation-decode | retain | operator-activation-decode | Required class and distinct selected work/shape. |
| operator-kv_write-decode | retain | operator-kv_write-decode | Required class and distinct selected work/shape. |
| operator-embedding-decode | omit_optional | none | Optional head/tail control outside the decoder; no native head/tail extension required by this package. |
| operator-lm_head-decode | omit_optional | none | Optional head/tail control outside the decoder; no native head/tail extension required by this package. |
| operator-attention_fused-decode | retain | operator-attention_fused-decode | Required class and distinct selected work/shape. |
| operator-rope-decode | merge | operator-q_projection-decode, operator-k_projection-decode | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| operator-cast-bf16-fp32-decode | merge | operator-q_projection-decode, operator-k_projection-decode | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| operator-cast-fp32-bf16-decode | merge | operator-q_projection-decode, operator-k_projection-decode | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| operator-q_projection-prefill | retain | operator-q_projection-prefill | Required class and distinct selected work/shape. |
| operator-k_projection-prefill | retain | operator-k_projection-prefill | Required class and distinct selected work/shape. |
| operator-v_projection-prefill | retain | operator-v_projection-prefill | Required class and distinct selected work/shape. |
| operator-qk_score-prefill | merge | operator-attention_fused-prefill | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-softmax-prefill | merge | operator-attention_fused-prefill | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-av_application-prefill | merge | operator-attention_fused-prefill | QK, softmax and AV remain explicit required work in the selected attention envelope; avoid duplicate silicon verdicts and fictitious score HBM traffic. |
| operator-output_projection-prefill | retain | operator-output_projection-prefill | Required class and distinct selected work/shape. |
| operator-normalization-prefill | retain | operator-normalization-prefill | Required class and distinct selected work/shape. |
| operator-residual_addition-prefill | retain | operator-residual_addition-prefill | Required class and distinct selected work/shape. |
| operator-ffn_up-prefill | retain | operator-ffn_up-prefill | Required class and distinct selected work/shape. |
| operator-ffn_gate-prefill | retain | operator-ffn_gate-prefill | Required class and distinct selected work/shape. |
| operator-ffn_down-prefill | retain | operator-ffn_down-prefill | Required class and distinct selected work/shape. |
| operator-activation-prefill | retain | operator-activation-prefill | Required class and distinct selected work/shape. |
| operator-kv_write-prefill | retain | operator-kv_write-prefill | Required class and distinct selected work/shape. |
| operator-embedding-prefill | omit_optional | none | Optional head/tail control outside the decoder; no native head/tail extension required by this package. |
| operator-lm_head-prefill | omit_optional | none | Optional head/tail control outside the decoder; no native head/tail extension required by this package. |
| operator-attention_fused-prefill | retain | operator-attention_fused-prefill | Required class and distinct selected work/shape. |
| operator-rope-prefill | merge | operator-q_projection-prefill, operator-k_projection-prefill | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| operator-cast-bf16-fp32-prefill | merge | operator-q_projection-prefill, operator-k_projection-prefill | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| operator-cast-fp32-bf16-prefill | merge | operator-q_projection-prefill, operator-k_projection-prefill | Partition Q and new-K rotary/cast work between their projection parents; each tensor counted once; no separate timing control required. |
| layer-b1-s1 | retain | layer-b1-s1 | Required class and distinct selected work/shape. |
| layer-b8-s1 | retain | layer-b8-s1 | Required class and distinct selected work/shape. |
| layer-b32-s1 | retain | layer-b32-s1 | Required class and distinct selected work/shape. |
| layer-b1-s128 | retain | layer-b1-s128 | Required class and distinct selected work/shape. |
| gather-p16-c2048 | retain | gather-p16-c2048 | Required class and distinct selected work/shape. |
| gather-p16-c2049 | correctness_only | none | Retain partial-tail arithmetic and refusal tests at both page sizes; full/tail timed cross-product is not required. |
| gather-p32-c2048 | retain | gather-p32-c2048 | Required class and distinct selected work/shape. |
| gather-p32-c2049 | correctness_only | none | Retain partial-tail arithmetic and refusal tests at both page sizes; full/tail timed cross-product is not required. |
| launch-minimal | retain | launch-minimal | Required class and distinct selected work/shape. |
