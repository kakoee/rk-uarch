"""Opt-in streaming pytest phase timings; unfinished streams are not pass receipts."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TextIO

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--timing-jsonl", help="New JSONL path for selected nodes and phase outcomes")


def pytest_configure(config: pytest.Config) -> None:
    path = config.getoption("--timing-jsonl")
    if path:
        config.pluginmanager.register(Timing(Path(path)), "verification-phase-timing")


class Timing:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.output: TextIO = path.open("x")
        self.started = time.monotonic()
        self.completed = 0
        self.planned = 0
        self.outcomes: Counter[str] = Counter()
        self.phase_seconds: dict[str, float] = defaultdict(float)
        self.emit("start")

    def emit(self, event: str, **fields: Any) -> None:
        self.output.write(
            json.dumps({"event": event, "elapsed_s": time.monotonic() - self.started, **fields})
            + "\n"
        )
        self.output.flush()

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.planned = len(session.items)
        self.emit("collection", nodeids=[i.nodeid for i in session.items], planned=self.planned)

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.emit("deselected", nodeids=[i.nodeid for i in items])

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.outcome != "passed":
            self.emit(
                "collection_outcome",
                nodeid=report.nodeid,
                outcome=report.outcome,
                detail=str(report.longrepr),
            )

    def pytest_runtest_logstart(self, nodeid: str, location: tuple[str, int | None, str]) -> None:
        self.emit("test_start", nodeid=nodeid, completed=self.completed, planned=self.planned)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.outcomes[report.when + ":" + report.outcome] += 1
        self.phase_seconds[report.when] += report.duration
        self.emit(
            "phase",
            nodeid=report.nodeid,
            when=report.when,
            outcome=report.outcome,
            duration_s=report.duration,
            detail=str(report.longrepr) if report.longrepr else None,
            wasxfail=getattr(report, "wasxfail", None),
        )
        if report.when == "teardown":
            self.completed += 1

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        self.emit(
            "finish",
            exitstatus=int(exitstatus),
            completed=self.completed,
            planned=self.planned,
            phase_outcomes=dict(self.outcomes),
            phase_seconds=dict(self.phase_seconds),
        )

    def pytest_unconfigure(self, config: pytest.Config) -> None:
        self.output.close()
