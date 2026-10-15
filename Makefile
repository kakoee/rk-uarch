# Lane A: native, image, table · Lane B: report, study, vendor-rk · both: golden-update
.PHONY: sync test test-fast lint typecheck imports gen gen-check golden-update vendor-rk table report \
        image native native-test demo-data

sync:        ; uv sync --extra dev
test:        ; uv run pytest -q
test-fast:   ; uv run pytest -q -m "not nightly and not silicon and not native"
lint:        ; uv run ruff check .
typecheck:
	uv run mypy src contract/uarch_contract scripts
	uv run mypy --no-explicit-package-bases contract/tests
imports:     ; uv run lint-imports
gen:         ; uv run python -m uarch_contract.generate
gen-check:   ; uv run python -m uarch_contract.generate --check
golden-update: ; @echo "make golden-update lands in U-P7"; exit 1
# Export values as data; the Python CLI parses optional shell-quoted PARAMS paths.
export SHA RK PARAMS
vendor-rk:   ; uv run --no-sync python scripts/vendor_rk.py
# Pass CLI arguments explicitly, e.g. make table ARGS='--help'.
ARGS ?= --help
table:       ; uv run uarch table $(ARGS)
report:      ; uv run uarch report $(ARGS)
image:       ; @echo "the engine image lands in U-P5 (Linux box only)"; exit 1
native:      ; cd native && cargo build --locked --offline --target x86_64-unknown-linux-gnu
native-test: ; cd native && cargo test --locked --offline --all-features --target x86_64-unknown-linux-gnu
demo-data:   ; @echo "demo data lands in U-P21"; exit 1
