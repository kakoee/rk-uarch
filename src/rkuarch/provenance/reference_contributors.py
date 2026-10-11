"""Semantic reference-input closure for the existing adopted U2 oracle profile.

No oracle, filesystem, administrative-review shortcut or new wire schema. Original
rows are reconstructed in inventory order using the pinned generator's exact JSON
encoding and checked against its raw manifest. Unknown profiles fail closed.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any, NoReturn

import yaml
from uarch_contract.comparison import ReferenceInventory
from uarch_contract.errors import ArtifactMissing, IncompleteMetricContributors
from uarch_contract.hashing import content_hash, resolve_artifact, sha256, strict_json_loads
from uarch_contract.report_context import MetricDependencies

Key = tuple[str, str, str]
CHANNELS = ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes", "duration_s")


def _refuse(detail: str) -> NoReturn:
    raise IncompleteMetricContributors("IncompleteMetricContributors: adopted reference " + detail)


def _raw(identity: str, artifacts: Mapping[str, Any]) -> bytes:
    value = artifacts[identity]
    if not isinstance(value, bytes) or sha256(value) != identity:
        _refuse("raw source identity")
    return value


def validate_reference_contributors(
    dependencies: MetricDependencies,
    inventory_hashes: tuple[str, ...],
    artifacts: Mapping[str, Any],
    *,
    read_raw: Callable[[str], bytes] | None = None,
) -> None:
    """Require each original input at its exact source, including recursive recipes.

    The inventory/reference model remains independently identified; actual model or
    equal-valued actual input selectors are not reference provenance. This checks
    semantic closure, not real measurement eligibility or a new adoption decision.
    """

    def raw(identity: str) -> bytes:
        value = read_raw(identity) if read_raw is not None else _raw(identity, artifacts)
        if sha256(value) != identity:
            _refuse("raw source identity")
        return value

    descriptors: dict[str, Any] = {}
    sources = {(s.artifact_hash, s.recipe.metric_path): s for s in dependencies.source_recipes}
    expanded: dict[tuple[str, str], set[Key]] = {}

    def leaves(key: tuple[str, str], active: frozenset[tuple[str, str]] = frozenset()) -> set[Key]:
        if key in expanded:
            return expanded[key]
        if key in active or key not in sources:
            _refuse("missing/cyclic source recipe")
        result: set[Key] = set()
        for selector in sources[key].recipe.selectors:
            result.add((selector.kind, selector.artifact_hash, selector.json_pointer))
            if selector.kind == "result_field":
                result.update(
                    leaves((selector.artifact_hash, selector.json_pointer), active | {key})
                )
        expanded[key] = result
        return result

    for inventory_hash in sorted(set(inventory_hashes)):
        inv = ReferenceInventory.model_validate(resolve_artifact(inventory_hash, artifacts))
        if inv.classification != "adopted_oracle":
            # Explicit synthetic controls grant no real eligibility.
            continue
        manifest = strict_json_loads(raw(inv.oracle_manifest_sha256))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
            _refuse("unsupported manifest profile")
        by_id: dict[str, tuple[str, dict[str, Any]]] = {}
        needed_ids = {f.fixture_id for f in inv.fixtures}
        row_sources = {
            h
            for key in sources
            if key[0] == inventory_hash
            for kind, h, _ in leaves(key)
            if kind == "prepared_content"
        }
        for identity in sorted(row_sources):
            value = resolve_artifact(identity, artifacts)
            if (
                isinstance(value, dict)
                and isinstance(value.get("id"), str)
                and value["id"] in needed_ids
                and "component_params_sha256" in value
                and "model_shape" in value
            ):
                if value["id"] in by_id and by_id[value["id"]][0] != identity:
                    _refuse("ambiguous original row")
                by_id[value["id"]] = (identity, value)
        if set(by_id) != needed_ids or len(needed_ids) != len(inv.fixtures):
            _refuse("complete original input fingerprint")
        original_rows = [by_id[f.fixture_id][1] for f in inv.fixtures]
        encoded = (
            json.dumps(original_rows, sort_keys=True, indent=2, allow_nan=False) + "\n"
        ).encode()
        rows_hash = "sha256:" + manifest["files"].get("parity/fixtures.json", "")
        if sha256(encoded) != rows_hash:
            # A declared selected inventory needs the original full raw member. Do
            # not authenticate a subset by its administrative review or ambient disk.
            try:
                all_rows = strict_json_loads(raw(rows_hash))
            except (KeyError, ArtifactMissing):
                _refuse("original full rows blob required for selected inventory")
            if not isinstance(all_rows, list) or any(not isinstance(r, dict) for r in all_rows):
                _refuse("original rows member shape")
            exact = {r.get("id"): r for r in all_rows}
            if len(exact) != len(all_rows) or any(
                exact.get(f.fixture_id) != by_id[f.fixture_id][1] for f in inv.fixtures
            ):
                _refuse("original selected row/manifest bytes")
        if inv.reference_model.version != manifest.get("rk_sha"):
            _refuse("reference model/oracle pin")
        for index, fixture in enumerate(inv.fixtures):
            original_hash, row = by_id[fixture.fixture_id]
            binding = resolve_artifact(fixture.component_binding_hash, artifacts)
            projected = binding.get("kind") == "uarch_projection"
            if binding.get("kind") not in ("uarch_projection", "upstream_only"):
                _refuse("unsupported component binding")
            raw_hash = (
                binding["projected_descriptor_bytes_sha256"]
                if projected
                else binding["component_bytes_sha256"]
            )
            if raw_hash not in descriptors:
                descriptors[raw_hash] = yaml.safe_load(raw(raw_hash))
            descriptor = descriptors[raw_hash]
            if (
                row["component_params_sha256"] != raw_hash.removeprefix("sha256:")
                or manifest["files"].get(row["component_params_file"])
                != row["component_params_sha256"]
                or row["rk_sha"] != manifest["rk_sha"]
                or binding["upstream_sha"] != manifest["rk_sha"]
                or descriptor["id"] != binding["component_id"]
            ):
                _refuse("original component/source binding")
            execution = resolve_artifact(binding["execution_model_hash"], artifacts)
            if (
                execution["kind"] != "scalar_efficiency"
                or execution["memory"] is not None
                or execution["compute"]["value"] != descriptor["execution_model"]["value"]["value"]
            ):
                _refuse("original execution efficiency")
            if (
                fixture.precision.model_dump(mode="json") != row["precision"]
                or fixture.tp != row["tp"]
                or any(
                    row["query"].get(k) != v
                    for k, v in fixture.query.model_dump(mode="json").items()
                )
                or row["counts_scope"] != "replica"
                or row["duration_scope"] != "one_tp_rank_no_collectives"
            ):
                _refuse("original precision/tp/query scope")
            expected: set[Key] = {
                ("prepared_content", original_hash, p)
                for p in ("/model", "/model_shape", "/query", "/precision", "/tp")
            }
            expected.update(
                (kind, inventory_hash, "/reference_model")
                for kind in ("model_assumption", "model_evidence")
            )
            timing = {("model_assumption", binding["execution_model_hash"], "/compute")}
            for name in (fixture.precision.compute.value + "_tflops", "hbm_bw"):
                if projected:
                    truth = resolve_artifact(binding["primary_export_hash"], artifacts)
                    matches = [i for i, p in enumerate(truth["params"]) if p["name"] == name]
                    if len(matches) != 1:
                        _refuse("original projected peak/bandwidth")
                    timing.add(
                        (
                            "hardware_leaf",
                            binding["primary_export_hash"],
                            f"/params/{matches[0]}/value",
                        )
                    )
                else:
                    timing.add(("hardware_leaf", content_hash(descriptor), "/params/" + name))
            for channel in CHANNELS:
                pointer = f"/fixtures/{index}/values/{channel}/value"
                key = (inventory_hash, pointer)
                if key not in sources:
                    _refuse(pointer)
                source = sources[key]
                purpose = "duration" if channel == "duration_s" else "counts"
                if (
                    source.model_identity_hash != content_hash(inv.reference_model)
                    or source.recipe.purpose != purpose
                    or source.recipe.granularity != "whole_iteration"
                    or not {"model_identity", "precision"}
                    <= set(source.recipe.applicable_dimensions)
                ):
                    _refuse("source model/purpose/scope " + pointer)
                required = expected | (timing if purpose == "duration" else set())
                if not required <= leaves(key):
                    _refuse("missing/wrong-source input " + pointer)
                value = getattr(fixture.values, channel)
                original = (
                    row["duration_s"]
                    if channel == "duration_s"
                    else None
                    if channel == "vector_ops" or row["counts"].get(channel) is None
                    else row["counts"][channel] / row["tp"]
                )
                state = (
                    "absent"
                    if channel == "vector_ops"
                    else "null"
                    if original is None
                    else "zero"
                    if original == 0
                    else "positive"
                )
                if value.value != original or value.state != state:
                    _refuse("original reference value " + pointer)
