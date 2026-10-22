"""Observational worker timings; no change to data, admission, or execution laws."""

from __future__ import annotations

import json
import resource
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch


def profile_worker(args, worker):
    measurements = {}

    def timed(label, function):
        def call(*positional, **keywords):
            start = time.perf_counter()
            try:
                return function(*positional, **keywords)
            finally:
                measurements[label] = measurements.get(label, 0.0) + time.perf_counter() - start

        return call

    start = time.perf_counter()
    with ExitStack() as stack:
        if args.worker == "check":
            from uarch_contract.reference import ReferenceJob, ReferenceResult

            from rkuarch.engines.native import ordinary, reference

            for module, name, label in (
                (ordinary, "replay", "replay_total_s"),
                (ordinary, "strict_json_loads", "dispatch_json_parse_s"),
                (reference, "load_reference_job", "reference_input_admission_total_s"),
                (reference, "strict_json_loads", "reference_input_json_parse_s"),
                (reference, "_decode_envelope", "output_json_parse_s"),
                (reference, "check_reference", "independent_check_s"),
                (reference, "canonical_json", "canonical_input_and_output_serialization_s"),
            ):
                stack.enter_context(patch.object(module, name, timed(label, getattr(module, name))))
            for model, label in (
                (ReferenceJob, "input_schema_validation_all_calls_s"),
                (ReferenceResult, "output_schema_validation_s"),
            ):
                stack.enter_context(
                    patch.object(
                        model, "model_validate", staticmethod(timed(label, model.model_validate))
                    )
                )
        elif args.worker == "prepare":
            from rkuarch.mapping import reference as mapping
            from rkuarch.workload import reference as workload

            for module, name, label in (
                (mapping, "map_reference", "mapping_and_bundle_validation_s"),
                (workload, "prepare_job", "job_assembly_and_validation_s"),
            ):
                stack.enter_context(patch.object(module, name, timed(label, getattr(module, name))))
        worker(args)
    measurements["worker_total_s"] = time.perf_counter() - start
    record = dict(
        unit=args.unit,
        stage=args.worker,
        kind="measured_wall_seconds",
        wall_seconds=measurements,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_rss_source="Linux getrusage(RUSAGE_SELF), process lifetime",
        nesting="Totals include their named subphases; do not sum inclusive totals.",
    )
    (Path(args.output) / (args.unit + "." + args.worker + ".timing.json")).write_text(
        json.dumps(record, indent=2) + "\n"
    )
