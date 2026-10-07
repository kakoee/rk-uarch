"""Portable selected trace input and replay metadata (ADRs 0043/0044)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rk.provenance import Metric


class TraceSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    limit_requests: Annotated[int, Field(ge=1, le=10000)]
    start_time_s: Annotated[float, Field(ge=0)] = 0
    end_time_s: float | None = None
    time_compression: Annotated[float, Field(gt=0)] = 1
    drop_failed: bool = True
    model: str | None = None
    log_type: str | None = None

    @model_validator(mode="after")
    def valid_window(self) -> TraceSelection:
        if self.end_time_s is not None and self.end_time_s <= self.start_time_s:
            raise ValueError("end_time_s must exceed start_time_s")
        return self


class TraceRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    arrival_time_s: Annotated[float, Field(ge=0)]
    prompt_tokens: Annotated[int, Field(ge=1)]
    output_tokens: Annotated[int, Field(ge=1)]


class TraceArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    dataset_id: str
    raw_sha256: str
    loader: str
    normalization_version: Literal["1"] = "1"
    selection: TraceSelection
    arrival_unit: Literal["s"] = "s"
    time_origin: Literal["first_selected_request"] = "first_selected_request"
    replication_policy: Literal["fixed_trace"] = "fixed_trace"
    requests: tuple[TraceRequest, ...]
    stream_hash: str


class TraceCatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    loader: str
    source_url: str
    source_pin: str
    sha256: str
    license: str
    citation: str
    citation_url: str
    state: Literal["not_configured", "missing", "present_unverified", "error"]
    detail: str


class TracePreview(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    artifact: TraceArtifact
    request_count: Metric
    duration_s: Metric
    prompt_p50_tokens: Metric
    prompt_p99_tokens: Metric
    output_p50_tokens: Metric
    output_p99_tokens: Metric
