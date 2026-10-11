"""Standalone preparation, captured replay, input validation and workload-selection output."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from pydantic import ValidationError
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.common import RK_SCHEMA_SNAPSHOT
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.hashing import canonical_json, spec_hash, strict_json_loads
from uarch_contract.model_card import ModelCard
from uarch_contract.prepared import PreparedBundle
from uarch_contract.report_context import ReportContext
from uarch_contract.request import RequestIntent

from rkuarch.report.command import report_command


def _json(path: Path) -> Any:
    return strict_json_loads(path.read_bytes())


def _bundle(args: argparse.Namespace) -> PreparedBundle:
    if args.prepared_input is not None:
        if any(
            (
                args.hardware,
                args.embedding_hits,
                args.synthetic_assignment,
                args.rank_index is not None,
                args.spec,
                args.precision is not None,
                args.tp is not None,
                args.grid,
                args.kv_precision,
                args.initial_state,
                args.analytic_mode,
            )
        ):
            raise ValueError("PreparedOverride: imported work cannot be overridden")
        from rkuarch.workload.prepared import load_prepared_input

        return load_prepared_input(args.prepared_input)
    if args.hardware is not None and args.spec is not None:
        raise ValueError("Choose positional spec or --hardware")
    args.hardware = args.hardware or args.spec
    if args.hardware is None:
        raise ValueError("--hardware is required with --intent")
    from rkuarch.workload.prepare import prepare

    raw = args.hardware.read_bytes()
    hardware = HardwareSpec.model_validate(
        yaml.safe_load(raw) if args.hardware.suffix in (".yaml", ".yml") else strict_json_loads(raw)
    )
    hits = (
        None if args.embedding_hits is None else tuple(tuple(v) for v in _json(args.embedding_hits))
    )
    if args.intent is not None:
        if any(
            (
                args.precision is not None,
                args.tp is not None,
                args.grid,
                args.kv_precision,
                args.initial_state,
                args.analytic_mode,
            )
        ):
            raise ValueError("IntentOverride: input intent already fixes these fields")
        intent = RequestIntent.model_validate(_json(args.intent))
    else:
        intent = _model_intent(args, hardware)
    return prepare(
        intent,
        hardware,
        rank_index=args.rank_index or 0,
        embedding_hits=hits,
        synthetic_assignment=args.synthetic_assignment,
    )


def _model_intent(args: argparse.Namespace, hardware: HardwareSpec) -> RequestIntent:
    from rkuarch.workload.identity import load_model_shape
    from rkuarch.workload.prepared import physical_assumptions

    model_path = Path(args.model)
    if not model_path.is_file():
        if args.model not in ("llama-3.1-8b", "llama-3.1-70b", "mixtral-8x7b"):
            raise ValueError("UnknownModel: supply a local model/shape sidecar")
        model_path = (
            Path(__file__).resolve().parents[2]
            / "contract/fixtures/model_shapes"
            / f"{args.model}.json"
        )
    model, shape = load_model_shape(model_path)
    if args.precision is None:
        raise ValueError("--precision required with --model")
    grid: Any = (
        _json(args.grid)
        if args.grid
        else dict(
            decode=dict(batch=[1], context_per_seq=[1]),
            prefill=dict(n=[1], L=[1]),
            frequency_ratio=[1.0],
        )
    )
    detail = dict(compute=0, noc=0, dram=0, sync="exact", layer_reuse=True)
    if hardware.shared_sram is not None:
        detail["shared_sram"] = "unrepresented"
    return RequestIntent.model_validate(
        dict(
            contract="uarch-contract/0.2",
            rk_schema_snapshot=RK_SCHEMA_SNAPSHOT,
            component_id=hardware.id,
            hardware_spec_hash=spec_hash(hardware),
            model=model,
            model_shape=shape,
            precision=dict(compute=args.precision, kv_cache=args.kv_precision or args.precision),
            tp=args.tp if args.tp is not None else 1,
            envelope=dict(
                decode=dict(
                    batch_max=max(grid["decode"]["batch"]),
                    context_per_seq_max=max(grid["decode"]["context_per_seq"]),
                ),
                prefill=dict(
                    prompt_tokens_max=max(grid["prefill"]["L"]),
                    prompts_per_iteration_max=max(grid["prefill"]["n"]),
                ),
            ),
            grid=grid,
            mapping_policy="analytic-ops@1",
            uarch_fidelity=detail,
            initial_state=args.initial_state or "steady",
            kv_layout=dict(block_size_tokens=16),
            visit_weights=None,
            seed=0,
            accounting="resolved-ops/1",
            analytic_mode=args.analytic_mode or "per_op",
            assumptions_hash=physical_assumptions().assumptions_hash,
            preparation_policy="balanced-tp/1",
        )
    )


def _compat_app(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="uarch")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "capture", "table", "characterize"):
        sub = commands.add_parser(name)
        route = sub.add_mutually_exclusive_group(required=True)
        route.add_argument("--prepared-input", type=Path)
        route.add_argument("--intent", type=Path)
        route.add_argument("--model")
        sub.add_argument("spec", type=Path, nargs="?")
        sub.add_argument("--precision")
        sub.add_argument("--kv-precision")
        sub.add_argument("--tp", type=int)
        sub.add_argument("--grid", type=Path)
        sub.add_argument("--initial-state", choices=("cold", "steady"))
        sub.add_argument("--analytic-mode", choices=("aggregate", "per_op"))
        sub.add_argument("--engine", choices=("analytic",), default="analytic")
        sub.add_argument("--hardware", type=Path)
        sub.add_argument("--embedding-hits", type=Path)
        sub.add_argument("--synthetic-assignment", action="store_true")
        sub.add_argument("--rank-index", type=int)
        sub.add_argument("--output", type=Path, required=True)
        if name in ("capture", "table"):
            sub.add_argument("--assumptions", type=Path, required=True)
            sub.add_argument("--workers", type=int, default=1)
        if name == "table":
            sub.add_argument("--capture-dir", type=Path)
            sub.add_argument("--context", type=Path, required=True)
            sub.add_argument("--model-card", type=Path, required=True)
            sub.add_argument("--artifact-dir", type=Path, required=True)
    export = commands.add_parser("rk-component")
    export.add_argument("spec", type=Path)
    export.add_argument("--component-id", required=True)
    export.add_argument("--execution-model", type=Path, required=True)
    export.add_argument("--oracle-compat", action="store_true")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "rk-component":
            from uarch_contract.exports import ExecutionModelInput

            from rkuarch.hw.export import export_component, project_for_oracle

            hardware = HardwareSpec.model_validate(yaml.safe_load(args.spec.read_bytes()))
            execution = ExecutionModelInput.model_validate(_json(args.execution_model))
            truth, derivation = export_component(
                hardware, execution, component_id=args.component_id
            )
            _write(args.output / "truth.json", canonical_json(truth).encode() + b"\n")
            _write(args.output / "derivation.json", canonical_json(derivation).encode() + b"\n")
            if args.oracle_compat:
                descriptor, binding = project_for_oracle(
                    hardware, truth, derivation, execution, upstream_sha=RK_SCHEMA_SNAPSHOT
                )
                _write(args.output / "oracle-compat.yaml", descriptor)
                _write(args.output / "binding.json", canonical_json(binding).encode() + b"\n")
            return
        if args.command == "table" and args.capture_dir is not None:
            if args.prepared_input is None or args.workers != 1:
                raise ValueError("CaptureReplay: requires --prepared-input and workers=1")
        bundle = _bundle(args)
        if args.command == "prepare":
            data = canonical_json(bundle).encode() + b"\n"
        elif args.command == "characterize":
            from rkuarch.workload.characterize import characterize, characterize_markdown

            selection_capture = characterize(bundle)
            markdown_path = args.output.with_suffix(".md")
            if markdown_path == args.output:
                raise ValueError("OutputConflict: JSON destination aliases Markdown companion")
            _write_characterization(
                args.output,
                canonical_json(selection_capture).encode() + b"\n",
                markdown_path,
                characterize_markdown(selection_capture).encode(),
            )
            return
        else:
            from rkuarch.table.build import build_table, capture, captured_artifacts, write_table

            assumptions = AssumptionSet.model_validate(_json(args.assumptions))
            if args.command == "table" and args.capture_dir is not None:
                from rkuarch.table.companions import load_captured_work

                captured = load_captured_work(args.capture_dir, bundle, assumptions)
            else:
                captured = capture(
                    bundle, assumptions=assumptions, workers=args.workers, subprocess_engine=True
                )
            if args.command == "capture":
                for h, value in captured_artifacts(captured).items():
                    _write(args.output / (h[7:] + ".json"), canonical_json(value).encode() + b"\n")
                return
            from rkuarch.table.artifacts import _complete_closure, _Files
            from rkuarch.table.companions import read_artifact_directory

            context = ReportContext.model_validate(_json(args.context))
            card = ModelCard.model_validate(_json(args.model_card))
            files = _Files(args.artifact_dir)
            # Retain the explicit package, including original raw reference/refusal inputs
            # whose identities are resolved inside validators rather than envelope fields.
            files.loaded.update(read_artifact_directory(args.artifact_dir, raw_blobs=True))
            files.loaded.update(captured_artifacts(captured))
            # capture validated this bundle; index its embedded spec before recipe closure.
            files.loaded[bundle.intent.hardware_spec_hash] = bundle.hardware_spec.model_dump(
                mode="json"
            )
            files.loaded[context.context_hash] = context.model_dump(mode="json")
            _complete_closure(context.context_hash, files)
            package = build_table(
                captured, context=context, model_card=card, artifacts=files.loaded
            )
            write_table(package, args.output)
            return
        _write(args.output, data)
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, str(exc) + "\n")


def _write(path: Path, data: bytes) -> None:
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"OutputConflict: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def _write_characterization(
    json_path: Path, json_bytes: bytes, md_path: Path, md_bytes: bytes
) -> None:
    """Preflight BOTH companions; never replace an existing file or follow output symlinks."""
    outputs = ((json_path, json_bytes), (md_path, md_bytes))
    for path, data in outputs:
        if path.is_symlink() or (
            path.exists() and (not path.is_file() or path.read_bytes() != data)
        ):
            raise ValueError(f"OutputConflict: {path}")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    for path, data in outputs:
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, no_args_is_help=True)


def _forward_command(ctx: typer.Context) -> None:
    """Retain A3's exact argument grammar for delivered commands during Typer registration."""
    assert ctx.info_name is not None
    _compat_app([ctx.info_name, *ctx.args])


for _name in ("prepare", "capture", "table", "characterize", "rk-component"):
    app.command(
        _name,
        add_help_option=False,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )(_forward_command)


def _validation_message(error: Exception) -> str:
    if not isinstance(error, ValidationError):
        return str(error)
    messages = []
    for item in error.errors(include_url=False, include_input=False):
        path = ""
        for part in item["loc"]:
            path += f"[{part}]" if isinstance(part, int) else ("." if path else "") + str(part)
        # Model-level hardware invariants already include the offending path in their message.
        messages.append((path + ": " if path else "") + item["msg"])
    return "\n".join(messages)


@app.command("validate")
def validate_command(
    spec: Annotated[Path, typer.Argument(help="HardwareSpec YAML or JSON.")],
) -> None:
    """List original sourced inputs and counts; this is input validation, not chip validation."""
    try:
        raw = spec.read_bytes()
        hardware = HardwareSpec.model_validate(
            yaml.safe_load(raw)
            if spec.suffix.lower() in (".yaml", ".yml")
            else strict_json_loads(raw)
        )
    except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
        typer.echo(_validation_message(exc), err=True)
        raise typer.Exit(2) from None
    groups: dict[str, list[str]] = {"Non-stub claims": [], "Stipulations": [], "Stubs": []}
    for path, value in sorted(sourced_leaves(hardware)):
        description = f"{path}: {value.value} {value.unit}"
        if value.kind == "stipulation":
            groups["Stipulations"].append(f"{description}; rationale={value.rationale!r}")
        elif value.provenance == "stub":
            groups["Stubs"].append(f"{description}; provenance=stub; source=null")
        else:
            groups["Non-stub claims"].append(
                f"{description}; provenance={value.provenance}; source={value.source!r}; "
                f"date={value.date!r}"
            )
    stubs, stipulations = len(groups["Stubs"]), len(groups["Stipulations"])
    claims = len(groups["Non-stub claims"]) + stubs
    lines = [
        f"Hardware: {hardware.id} ({hardware.design_status})",
        f"Spec hash: {spec_hash(hardware)}",
        f"Sourced values: {claims + stipulations}",
        f"Claims: {claims} (including {stubs} stubs)",
        f"Stipulations: {stipulations}",
    ]
    for label, entries in groups.items():
        lines.extend(["", f"{label} ({len(entries)})", *("- " + entry for entry in entries)])
    typer.echo("\n".join(lines))


app.command("report")(report_command)


@app.command("assumptions")
def assumptions_command(
    output: Annotated[Path, typer.Option("--output")],
    model: Annotated[str, typer.Option("--model")] = "physical-resolved",
) -> None:
    """Export the current physical analytic declaration; no review or evidence authority."""
    from rkuarch.table.companions import write_outputs
    from rkuarch.workload.prepared import physical_assumptions

    try:
        if model != "physical-resolved":
            raise ValueError("UnsupportedModel: assumptions supports physical-resolved")
        write_outputs({output: canonical_json(physical_assumptions()).encode() + b"\n"})
    except (ValueError, TypeError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from None


companions_app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
app.add_typer(companions_app, name="companions")


@companions_app.command("draft")
def companions_draft_command(
    prepared_input: Annotated[Path, typer.Option("--prepared-input")],
    assumptions: Annotated[Path, typer.Option("--assumptions")],
    capture_dir: Annotated[Path, typer.Option("--capture-dir")],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    """Draft intrinsic dependencies and a STUB card; stop for actual independent review."""
    from rkuarch.table.companions import draft_companions, load_captured_work, write_outputs
    from rkuarch.workload.prepared import load_prepared_input

    try:
        c = load_captured_work(
            capture_dir,
            load_prepared_input(prepared_input),
            AssumptionSet.model_validate(_json(assumptions)),
        )
        card, deps, subject = draft_companions(c)
        write_outputs(
            {
                output / "model-card.json": canonical_json(card).encode() + b"\n",
                output / "metric-dependencies.json": canonical_json(deps).encode() + b"\n",
                output / "review-subject.txt": (subject + "\n").encode(),
                output / "README.txt": (
                    "UNREVIEWED declarations; not verified artifacts.\n"
                    "The all-zero review_hash is unresolved; no ReviewRecord is issued.\n"
                    "Review exact dependencies and every supplied comparison attempt externally.\n"
                    "Supply an independently reviewed family registry "
                    "and both real review records.\n"
                    "Assembly binds those explicit reviews; it does not issue or approve them.\n"
                    "Review subject (changes if declarations change): " + subject + "\n"
                    "STUB; error unknown; energy unverified. See table/companions.md.\n"
                ).encode(),
            }
        )
    except (ValueError, TypeError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from None
    typer.echo("UNREVIEWED draft written; stop for actual independent declaration reviews.")


@companions_app.command("assemble")
def companions_assemble_command(
    prepared_input: Annotated[Path, typer.Option("--prepared-input")],
    assumptions: Annotated[Path, typer.Option("--assumptions")],
    capture_dir: Annotated[Path, typer.Option("--capture-dir")],
    recipes: Annotated[Path, typer.Option("--recipes")],
    recipe_review: Annotated[Path, typer.Option("--recipe-review")],
    registry: Annotated[Path, typer.Option("--registry")],
    registry_review: Annotated[Path, typer.Option("--registry-review")],
    model_card: Annotated[Path, typer.Option("--model-card")],
    artifact_dir: Annotated[Path, typer.Option("--artifact-dir")],
    output: Annotated[Path, typer.Option("--output")],
    comparison: Annotated[list[Path] | None, typer.Option("--comparison")] = None,
    no_comparisons: Annotated[bool, typer.Option("--no-comparisons")] = False,
) -> None:
    """Bind supplied declaration reviews and delegate policy/assembly to B's public helper."""
    from uarch_contract.comparison import ComparisonArtifact
    from uarch_contract.evidence import ReviewRecord
    from uarch_contract.hashing import content_hash, verify_identity
    from uarch_contract.registry import FamilyRegistry
    from uarch_contract.report_context import MetricDependencies

    from rkuarch.table.build import captured_artifacts
    from rkuarch.table.companions import (
        UNREVIEWED,
        add_artifact,
        load_captured_work,
        read_artifact_directory,
        write_outputs,
    )
    from rkuarch.workload.prepared import load_prepared_input

    try:
        if bool(comparison) == no_comparisons:
            raise ValueError("ComparisonIntake: choose --comparison or explicit --no-comparisons")
        c = load_captured_work(
            capture_dir,
            load_prepared_input(prepared_input),
            AssumptionSet.model_validate(_json(assumptions)),
        )
        store = (
            read_artifact_directory(artifact_dir, raw_blobs=True) if artifact_dir.exists() else {}
        )
        for value in captured_artifacts(c).values():
            add_artifact(store, value)
        add_artifact(store, c.bundle.hardware_spec)
        deps = MetricDependencies.model_validate(_json(recipes))
        family = FamilyRegistry.model_validate(_json(registry))
        card = ModelCard.model_validate(_json(model_card))
        dep_review = ReviewRecord.model_validate(_json(recipe_review))
        fam_review = ReviewRecord.model_validate(_json(registry_review))
        verify_identity(deps, "dependencies_hash")
        verify_identity(family, "registry_hash")
        for declaration, review, path in (
            (deps, dep_review, recipes),
            (family, fam_review, registry),
        ):
            if declaration.review_hash not in (UNREVIEWED, review.review_hash):
                raise ValueError(f"ReviewBindingMismatch: {path}: existing review differs")
            add_artifact(store, review)
        # Bind only the explicitly supplied records. B validates their actual subjects,
        # decisions, independence, family, source closure and comparison completeness.
        deps = deps.model_copy(update={"review_hash": dep_review.review_hash})
        deps = deps.model_copy(
            update={"dependencies_hash": content_hash(deps, exclude=("dependencies_hash",))}
        )
        family = family.model_copy(update={"review_hash": fam_review.review_hash})
        family = family.model_copy(
            update={"registry_hash": content_hash(family, exclude=("registry_hash",))}
        )
        for value in (deps, family, card):
            add_artifact(store, value)
        comparisons = tuple(ComparisonArtifact.model_validate(_json(p)) for p in comparison or [])
        identities = tuple(add_artifact(store, value) for value in comparisons)
        if len(set(identities)) != len(identities):
            raise ValueError("ComparisonIntake: duplicate --comparison")
        try:
            from rkuarch.provenance.companions import assemble_stub_context
        except ModuleNotFoundError as exc:
            if exc.name != "rkuarch.provenance.companions":
                raise
            raise ValueError("PeerImplementationMissing: rkuarch.provenance.companions") from exc
        context, package = assemble_stub_context(
            c,
            dependencies=deps,
            registry=family,
            model_card=card,
            comparison_hashes=identities,
            artifacts=store,
        )
        context = ReportContext.model_validate(context)
        verify_identity(context, "context_hash")
        outputs = {}
        for identity, value in package.items():
            if isinstance(value, bytes):
                from uarch_contract.hashing import sha256

                if sha256(value) != identity:
                    raise ValueError(f"ArtifactHashMismatch: returned bytes {identity}")
                data = value
            else:
                if add_artifact({}, value) != identity:
                    raise ValueError(f"ArtifactHashMismatch: returned object {identity}")
                data = canonical_json(value).encode() + b"\n"
            outputs[artifact_dir / (identity[7:] + ".json")] = data
        context_bytes = canonical_json(context).encode() + b"\n"
        outputs[artifact_dir / (context.context_hash[7:] + ".json")] = context_bytes
        if output in outputs and outputs[output] != context_bytes:
            raise ValueError(f"OutputConflict: {output}")
        outputs[output] = context_bytes
        write_outputs(outputs)
    except (ValueError, TypeError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from None
    typer.echo("Offline context assembled from supplied reviews; STUB, energy unverified.")


if __name__ == "__main__":
    app()
