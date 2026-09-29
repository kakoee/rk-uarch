# rkuarch — the harness

request → workload (op graph) → mapping (TaskGraph) → engine (EngineJob → EngineResult)
→ table (rows, interpolation, measured errors) → provenance (badges, conditional_on)
→ report / study. Never imports rk. The engines live behind one protocol; the table
does not know which engine ran except through EngineResult.fidelity_detail.
