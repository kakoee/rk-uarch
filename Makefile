# Lane A: native, image, table · Lane B: report, study, vendor-rk · both: golden-update
.PHONY: sync test test-fast lint typecheck imports gen gen-check golden-update vendor-rk table report \
        image native native-test demo-data

sync:        ; uv sync --extra dev
test:        ; uv run pytest -q
test-fast:   ; uv run pytest -q -m "not nightly and not silicon and not native"
lint:        ; uv run ruff check .
typecheck:   ; uv run mypy
imports:     ; uv run lint-imports
gen:         ; uv run python -m uarch_contract.generate
gen-check:   ; uv run python -m uarch_contract.generate --check
golden-update: ; @echo "make golden-update lands in U-P7"; exit 1
# Export values as data; the Python CLI parses optional shell-quoted PARAMS paths.
export SHA RK PARAMS
vendor-rk:   ; uv run --no-sync python scripts/vendor_rk.py
table:       ; @echo "uarch table lands in U-P3"; exit 1
report:      ; @echo "uarch report lands in U-P4"; exit 1
image:       ; @echo "the engine image lands in U-P5 (Linux box only)"; exit 1
native:      ; @echo "the native engine (Rust, cargo) lands in U-P11a"; exit 1
native-test: ; @echo "native tests (cargo test) land in U-P11a"; exit 1
demo-data:   ; @echo "demo data lands in U-P21"; exit 1
