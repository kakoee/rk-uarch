# Lane A: native, image, table · Lane B: report, study, vendor-rk · both: golden-update
.PHONY: sync test test-fast lint typecheck imports gen golden-update vendor-rk table report \
        image native native-test demo-data

sync:        ; uv sync --extra dev
test:        ; uv run pytest -q
test-fast:   ; uv run pytest -q -m "not nightly and not silicon and not native"
lint:        ; uv run ruff check .
typecheck:   ; uv run mypy
imports:     ; uv run lint-imports
gen:         ; @echo "make gen lands in U-P1 (contract JSON Schema)"; exit 1
golden-update: ; @echo "make golden-update lands in U-P7"; exit 1
vendor-rk:   ; @echo "make vendor-rk SHA=<sha> RK=<path> lands in U-P2"; exit 1
table:       ; @echo "uarch table lands in U-P3"; exit 1
report:      ; @echo "uarch report lands in U-P4"; exit 1
image:       ; @echo "the engine image lands in U-P5 (Linux box only)"; exit 1
native:      ; @echo "the native engine lands in U-P11"; exit 1
native-test: ; @echo "native tests land in U-P11"; exit 1
demo-data:   ; @echo "demo data lands in U-P21"; exit 1
