"""Input version admission and named, non-mutating legacy migrations (ADR 0040)."""
from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, field_validator, model_validator


def _v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    return {'schema_version': '1', **raw}


def migrate_scenario_v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    return _v0_to_v1(raw)


def migrate_system_v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    return _v0_to_v1(raw)


def migrate_plan_v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    return _v0_to_v1(raw)


def migrate_workload_v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    return _v0_to_v1(raw)


def require_version(value: object, field: str) -> Literal['1']:
    if not isinstance(value, str) or value != '1':
        raise ValueError(f'{field}.schema_version: unsupported version {value!r}; expected "1"')
    return '1'


class VersionedInput(BaseModel):
    input_kind: ClassVar[str]
    schema_version: Literal['1', '2'] = '1'

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy(cls, raw: Any) -> Any:
        if isinstance(raw, dict) and 'schema_version' not in raw:
            return {'system': migrate_system_v0_to_v1,
                    'execution_plan': migrate_plan_v0_to_v1,
                    'workload': migrate_workload_v0_to_v1}[cls.input_kind](raw)
        return raw

    @field_validator('schema_version', mode='before')
    @classmethod
    def known_version(cls, value: object) -> Literal['1', '2']:
        if cls.input_kind == 'system' and value == '2':
            return '2'
        return require_version(value, cls.input_kind)


def input_v1_hash_payload(model: BaseModel) -> Any:
    """Canonical identity projection: v1 metadata adds no semantic information."""
    payload = model.model_dump(mode='json')

    def project(value: Any, dumped: Any) -> Any:
        if isinstance(value, BaseModel) and isinstance(dumped, dict):
            if isinstance(value, VersionedInput) and value.schema_version == '1':
                dumped.pop('schema_version', None)
                if value.input_kind == 'system':
                    for key in ('economics', 'vcpus_per_gpu'):
                        if dumped.get(key) is None:
                            dumped.pop(key, None)
            for key in tuple(dumped):
                if key in type(value).model_fields:
                    dumped[key] = project(getattr(value, key), dumped[key])
        elif isinstance(value, (tuple, list)) and isinstance(dumped, list):
            return [project(v, d) for v, d in zip(value, dumped, strict=True)]
        elif isinstance(value, dict) and isinstance(dumped, dict):
            return {k: project(value[k], d) for k, d in dumped.items()}
        return dumped

    return project(model, payload)
