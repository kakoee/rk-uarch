"""Eight PrecisionFormat members copied from rk-sim at U0001's exact pin."""

from enum import StrEnum

from .common import FrozenModel


class PrecisionFormat(StrEnum):
    FP32 = "fp32"
    TF32 = "tf32"
    BF16 = "bf16"
    FP16 = "fp16"
    FP8 = "fp8"
    INT8 = "int8"
    FP4 = "fp4"
    INT4 = "int4"


class Precision(FrozenModel):
    compute: PrecisionFormat = PrecisionFormat.FP16
    kv_cache: PrecisionFormat = PrecisionFormat.FP16
