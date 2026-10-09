"""Sourced U0003 hardware derivation; no fitted execution efficiency."""

from __future__ import annotations

import math
from typing import Literal, cast

from uarch_contract.derivation import Derivation, DerivedParameter
from uarch_contract.errors import UnsupportedPrecision
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.precision import Precision, PrecisionFormat
from uarch_contract.sourced import Calibration, SourcedValue

from rkuarch.engines.protocol import ResolvedHardware

FORMAT_BYTES = {
    PrecisionFormat(k): v
    for k, v in dict(fp32=4, tf32=4, bf16=2, fp16=2, fp8=1, int8=1, fp4=0.5, int4=0.5).items()
}


def validate_storage(spec: HardwareSpec, fmt: PrecisionFormat) -> None:
    if fmt not in spec.formats:
        raise ValueError(f"UnsupportedKvStorage: formats.{fmt}")
    if spec.formats[fmt].bytes != FORMAT_BYTES[fmt]:
        raise UnsupportedPrecision(f"UnsupportedPrecision: formats.{fmt}.bytes")
    if spec.formats[fmt].block_scale_bytes.value != 0:
        raise ValueError(f"UnsupportedBlockScaleGeometry: formats.{fmt}.block_scale_bytes")


def resolved_frequencies(spec: HardwareSpec, frequency_ratio: float) -> tuple[int, int, int]:
    if not math.isfinite(frequency_ratio) or frequency_ratio <= 0:
        raise ValueError("UnsupportedFrequency: frequency_ratio")
    if spec.clock_domains.dram.scales_with_core and frequency_ratio != 1:
        raise ValueError("UnsupportedDramFrequencyScaling: clock_domains.dram")
    result = []
    for name in ("core", "noc", "dram"):
        domain = getattr(spec.clock_domains, name)
        raw = domain.freq_hz.value * (frequency_ratio if domain.scales_with_core else 1)
        if not math.isfinite(raw) or raw < 0.5:
            raise ValueError(f"UnsupportedFrequency: clock_domains.{name}")
        hz = round(raw)
        if hz < 1:
            raise ValueError(f"UnsupportedFrequency: clock_domains.{name}")
        result.append(hz)
    return result[0], result[1], result[2]


def derive_rk_params(spec: HardwareSpec) -> Derivation:
    """Return the accepted Derivation, including values and exact source paths."""
    spec = HardwareSpec.model_validate(spec)
    core_hz, _, _ = resolved_frequencies(spec, 1.0)
    leaves = dict(sourced_leaves(spec))
    identity = spec_hash(spec)
    parameters = []

    def parameter(
        name: str, number: float, unit: str, formula: str, paths: tuple[str, ...]
    ) -> None:
        paths = tuple(sorted(paths))
        conditions = tuple(p for p in paths if leaves[p].kind == "stipulation")
        claims = [leaves[p].provenance for p in paths if leaves[p].kind == "claim"]
        order = [
            Calibration.MEASURED,
            Calibration.SPEC_DERIVED,
            Calibration.ESTIMATED,
            Calibration.STUB,
        ]
        badge = max((c for c in claims if c is not None), key=order.index, default=None)
        if conditions:
            value = SourcedValue(
                value=number,
                unit=unit,
                kind="stipulation",
                rationale=formula + ": " + ", ".join(conditions),
            )
        else:
            value = SourcedValue(
                value=number,
                unit=unit,
                kind="claim",
                provenance=badge,
                source=None if badge == Calibration.STUB else f"uarch-derive:{identity}:{formula}",
            )
        parameters.append(
            DerivedParameter(
                name=name,
                value=value,
                formula_id=formula,
                contributor_paths=paths,
                conditional_paths=conditions,
                claim_badge=cast(
                    Literal["measured", "spec_derived", "estimated", "stub"] | None, badge
                ),
            )
        )

    cores = int(spec.cores.grid.rows.value) * int(spec.cores.grid.cols.value)
    for fmt, rate in sorted(spec.cores.core_type.matrix_engine.macs_per_cycle.items()):
        if fmt not in spec.formats:
            raise UnsupportedPrecision(f"UnsupportedPrecision: compute format {fmt} has no storage")
        validate_storage(spec, fmt)
        integer = fmt in (PrecisionFormat.INT8, PrecisionFormat.INT4)
        parameter(
            fmt.value + ("_tops" if integer else "_tflops"),
            2 * cores * rate.value * core_hz / 1e12,
            "TOPS" if integer else "TFLOPS",
            "matrix-peak/1",
            (
                "cores.grid.rows",
                "cores.grid.cols",
                "clock_domains.core.freq_hz",
                f"cores.core_type.matrix_engine.macs_per_cycle.{fmt}",
            ),
        )
    parameter(
        "hbm_bw",
        spec.memory.dram.bw_bytes_per_s.value / 1e12,
        "TB/s",
        "decimal-bandwidth/1",
        ("memory.dram.bw_bytes_per_s",),
    )
    parameter(
        "hbm_capacity",
        spec.memory.dram.capacity_bytes.value / 1e9,
        "GB",
        "decimal-capacity/1",
        ("memory.dram.capacity_bytes",),
    )
    parameter("tdp", spec.tdp_w.value, "W", "identity/1", ("tdp_w",))
    result = Derivation(
        format="uarch-derivation/1",
        hardware_spec_hash=identity,
        parameters=tuple(parameters),
        derivation_hash="sha256:" + "0" * 64,
    )
    return result.model_copy(
        update={"derivation_hash": content_hash(result, exclude=("derivation_hash",))}
    )


def resolve_hardware(
    spec: HardwareSpec, precision: Precision, *, frequency_ratio: float = 1.0
) -> ResolvedHardware:
    """Resolve the physical model's numeric hardware; execution efficiency is absent."""
    spec = HardwareSpec.model_validate(spec)
    precision = Precision.model_validate(precision)
    compute = spec.cores.core_type.matrix_engine.macs_per_cycle
    if precision.compute not in compute:
        raise UnsupportedPrecision(f"UnsupportedPrecision: matrix peak {precision.compute}")
    validate_storage(spec, precision.compute)
    validate_storage(spec, precision.kv_cache)
    core, noc, dram = resolved_frequencies(spec, frequency_ratio)
    cores = int(spec.cores.grid.rows.value) * int(spec.cores.grid.cols.value)
    capacity = spec.memory.dram.capacity_bytes.value
    if not capacity.is_integer():
        raise ValueError("ParamsMismatch: DRAM capacity requires integral bytes")
    return ResolvedHardware(
        array_rows=int(spec.cores.core_type.matrix_engine.array.rows.value),
        array_cols=int(spec.cores.core_type.matrix_engine.array.cols.value),
        core_freq_hz=core,
        noc_freq_hz=noc,
        dram_freq_hz=dram,
        hardware_spec_hash=spec_hash(spec),
        matrix_peak_ops_per_s=2 * cores * compute[precision.compute].value * core,
        vector_peak_ops_per_s=cores * spec.cores.core_type.vector_engine.ops_per_cycle.value * core,
        dram_bw_bytes_per_s=spec.memory.dram.bw_bytes_per_s.value,
        dram_capacity_bytes=int(capacity),
    )
