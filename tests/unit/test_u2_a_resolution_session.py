"""RC-P1: independent ownership/cost assertions, never bypass semantic validation."""

from collections import Counter
from copy import deepcopy

import pytest
from uarch_contract import comparison, hashing
from uarch_contract.report_context import validate_metric_dependencies, validate_report_context

from tests.unit.test_u2_a_artifacts import artifacts, read


@pytest.mark.parametrize("boundary", ["dependencies", "context"])
def test_one_authentication_and_parse_per_identity_with_all_ratio_checks(boundary, monkeypatch):
    store = artifacts()
    calls, parses, actual = Counter(), Counter(), []
    identity = hashing.artifact_identity
    check = comparison._validate_actual_source

    def authenticate(value):
        key = identity(value)
        calls[key] += 1
        # No caller dictionary, including its nested lists, is admitted to the cache.
        if key in store:
            assert value is not store[key]
            for name, item in value.items():
                if isinstance(item, (dict, list)):
                    assert item is not store[key][name]
        return key

    def source_check(channel, *args):
        actual.append(channel.channel)
        return check(channel, *args)

    monkeypatch.setattr(hashing, "artifact_identity", authenticate)
    monkeypatch.setattr(comparison, "_validate_actual_source", source_check)
    for model in (comparison.ComparisonArtifact, comparison.ReferenceInventory):
        original = model.model_validate

        def parse(cls, value, _original=original, **kw):
            parses[cls.__name__] += 1
            return _original(value, **kw)

        monkeypatch.setattr(model, "model_validate", classmethod(parse))
    d = read("metric-dependencies.json")
    if boundary == "dependencies":
        terminals = validate_metric_dependencies(d, store)
        # Independent literal contributor expectations are preserved, including two models.
        timing = terminals["/comparisons/0/fixtures/0/channels/4/raw_rel"]
        assert len({s.artifact_hash for s in timing if s.kind == "model_evidence"}) == 2
        assert any(s.json_pointer == "/memory/dram/bw_bytes_per_s" for s in timing)
    else:
        validate_report_context(read("r2-semantic-context.json"), store)
    ratios = [r for r in d["recipes"] if r["metric_path"].startswith("/comparisons/")]
    assert len(actual) == len(ratios) * (2 if boundary == "context" else 1)
    assert calls and max(calls.values()) == 1
    assert parses == {"ComparisonArtifact": 1, "ReferenceInventory": 1}


@pytest.mark.parametrize("boundary", ["dependencies", "context"])
def test_later_call_cannot_reuse_success_for_changed_nested_bytes(boundary):
    store = artifacts()
    value = read(
        "metric-dependencies.json" if boundary == "dependencies" else "r2-semantic-context.json"
    )
    validate = (
        validate_metric_dependencies if boundary == "dependencies" else validate_report_context
    )
    original = deepcopy(store)
    validate(value, store)
    assert store == original
    d = read("metric-dependencies.json")
    target = next(
        s["artifact_hash"]
        for r in d["recipes"]
        for s in r["selectors"]
        if s["kind"] == "model_assumption"
        and store[s["artifact_hash"]].get("format") == "uarch-comparison/1"
    )
    store[target]["fixtures"][0]["channels"][0]["actual"]["value"] += 1
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        validate(value, store)


def closure():
    raw = b"explicit raw test observation\n"
    raw_hash = hashing.sha256(raw)
    source = {"format": "uarch-reference-source/1", "raw_blob_sha256": raw_hash}
    source["source_hash"] = hashing.artifact_identity(source)
    leaf = {
        "nested": {"value": 3},
        "capture_source": {
            "artifact_hash": source["source_hash"],
            "json_pointer": "/raw_blob_sha256",
        },
    }
    leaf_hash = hashing.artifact_identity(leaf)
    review = {"synthetic": "identity closure only, not a ReviewRecord"}
    review_hash = hashing.artifact_identity(review)
    root = {
        "format": "uarch-metric-dependencies/1",
        "review_hash": review_hash,
        "recipes": [
            {"selectors": [{"artifact_hash": leaf_hash, "json_pointer": "/nested/value"}]}
            for _ in range(4)
        ],
        "source_recipes": [],
    }
    root["dependencies_hash"] = hashing.artifact_identity(root)
    return (
        root["dependencies_hash"],
        {
            root["dependencies_hash"]: root,
            leaf_hash: leaf,
            source["source_hash"]: source,
            raw_hash: raw,
            review_hash: review,
        },
        leaf_hash,
        raw_hash,
    )


def test_closure_authenticates_once_but_checks_every_pointer(monkeypatch):
    root, store, leaf, raw = closure()
    count, pointers = Counter(), []
    identity, pointer = hashing.artifact_identity, hashing.resolve_pointer

    def auth(value):
        key = identity(value)
        count[key] += 1
        assert value is not store[key]
        return key

    def follow(value, path):
        pointers.append(path)
        return pointer(value, path)

    monkeypatch.setattr(hashing, "artifact_identity", auth)
    monkeypatch.setattr(hashing, "resolve_pointer", follow)
    assert hashing.verify_declared_artifact_closure(root, store) == tuple(sorted(store))
    assert count[leaf] == 1 and max(count.values()) == 1
    assert pointers.count("/nested/value") == 4
    assert pointers.count("/raw_blob_sha256") == 1


@pytest.mark.parametrize("change", ["nested", "raw", "missing_raw", "pointer"])
def test_closure_later_mutation_and_bad_pointer_refuse(change):
    root, store, leaf, raw = closure()
    hashing.verify_declared_artifact_closure(root, store)
    if change == "nested":
        store[leaf]["nested"]["value"] += 1
    elif change == "raw":
        store[raw] += b"changed"
    elif change == "missing_raw":
        del store[raw]
    else:
        value = store[root]
        value["recipes"][-1]["selectors"][0]["json_pointer"] = "/nested/missing"
        root = hashing.artifact_identity(value)
        value["dependencies_hash"] = root
        store[root] = value
    with pytest.raises(
        ValueError, match="ArtifactHashMismatch|ArtifactMissing|InvalidArtifactPointer"
    ):
        hashing.verify_declared_artifact_closure(root, store)


def test_public_resolver_still_returns_caller_value_and_reauthenticates():
    value = {"nested": [1]}
    key = hashing.artifact_identity(value)
    store = {key: value}
    assert hashing.resolve_artifact(key, store) is value
    value["nested"].append(2)
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        hashing.resolve_artifact(key, store)


def test_caller_mutation_after_authentication_cannot_change_private_snapshot(monkeypatch):
    store = artifacts()
    context = read("r2-semantic-context.json")
    target = context["comparison_hashes"][0]
    original = hashing.artifact_identity
    changed = False

    def mutate_caller(value):
        nonlocal changed
        key = original(value)
        if key == target and not changed:
            changed = True
            store[target]["fixtures"][0]["channels"][0]["actual"]["value"] += 17
        return key

    monkeypatch.setattr(hashing, "artifact_identity", mutate_caller)
    validated = validate_report_context(context, store)
    assert changed and validated.context_hash == context["context_hash"]
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        validate_report_context(context, store)


def test_rehashed_duplicate_inventory_and_changed_index_mapping_refuse():
    from tests.unit.test_u2_a_artifacts import correction_rebind

    context, d, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    validate_report_context(context, store)
    old_comparison = context["comparison_hashes"][0]
    c = deepcopy(store[old_comparison])
    old_inventory = c["reference_inventory_hash"]
    inv = deepcopy(store[old_inventory])
    inv["fixtures"].append(deepcopy(inv["fixtures"][0]))
    inv["inventory_hash"] = hashing.artifact_identity(inv)
    c["reference_inventory_hash"] = inv["inventory_hash"]
    c["comparison_hash"] = hashing.artifact_identity(c)
    replacements = {old_inventory: inv["inventory_hash"], old_comparison: c["comparison_hash"]}

    def replace(value):
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        return replacements.get(value, value) if isinstance(value, str) else value

    d, context = replace(d), replace(context)
    store[inv["inventory_hash"]] = inv
    store[c["comparison_hash"]] = c
    correction_rebind(context, d, store)
    with pytest.raises(ValueError, match="IncompleteMetricContributors.*reference fixture"):
        validate_report_context(context, store)

    context, store = read("r2-semantic-context.json"), artifacts()
    validate_report_context(context, store)
    other = deepcopy(store[context["comparison_hashes"][0]])
    other["limitations"].append("Distinct synthetic comparison identity for index substitution.")
    other["comparison_hash"] = hashing.artifact_identity(other)
    store[hashing.artifact_identity(other)] = other
    context["comparison_hashes"] = [hashing.artifact_identity(other)]
    context["context_hash"] = hashing.artifact_identity(context)
    with pytest.raises(ValueError, match="IncompleteMetricContributors|RefusalSourceMismatch"):
        validate_report_context(context, store)


def test_dictionary_copy_hook_cannot_retain_caller_ownership(monkeypatch):
    class CallerDict(dict):
        def __deepcopy__(self, memo):
            return self

    context, store = read("r2-semantic-context.json"), artifacts()
    key = context["comparison_hashes"][0]
    store[key] = CallerDict(store[key])
    original = hashing.artifact_identity

    def authenticate(value):
        identity = original(value)
        if identity == key:
            assert value is not store[key]
            assert value["fixtures"] is not store[key]["fixtures"]
        return identity

    monkeypatch.setattr(hashing, "artifact_identity", authenticate)
    validate_report_context(context, store)


def test_detachment_does_not_normalize_invalid_nested_models():
    from pydantic import BaseModel

    class Payload(BaseModel):
        n: int

    model = Payload(n=1)
    top_key = hashing.artifact_identity(model.model_dump(mode="json"))
    assert hashing.verify_declared_artifact_closure(top_key, {top_key: model}) == (top_key,)
    invalid = {"nested": model}
    key = hashing.artifact_identity({"nested": {"n": 1}})
    with pytest.raises(TypeError):
        hashing.resolve_artifact(key, {key: invalid})
    with pytest.raises(TypeError):
        hashing.verify_declared_artifact_closure(key, {key: invalid})
