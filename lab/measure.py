"""Capture actual execution plans and defensible timings.

Every number this module produces is a median of N runs after a discarded
warm-up. A single run measures the buffer pool, not the plan, and a mean is
hostage to one outlier. If you see a single-run performance number in a README
anywhere, that is the tell.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from lab.sqlcmd import run_sql, run_sql_file, run_sql_plan, run_sql_timed

DB = "PlanLab"
REPO_ROOT = Path(__file__).resolve().parent.parent

# SET STATISTICS TIME emits one of these per statement. The parse-and-compile
# line reports its own elapsed time, so the interesting figure is the last.
_ELAPSED = re.compile(r"elapsed time = (\d+) ms", re.IGNORECASE)

# Presence of this file means the pathology depends on a warm plan cache and
# clearing it would destroy the effect being demonstrated.
KEEP_CACHE_MARKER = "KEEP_PLAN_CACHE"


@dataclass
class Measurement:
    label: str
    runs_ms: list[float]
    plan_xml: str

    @property
    def median_ms(self) -> float:
        return statistics.median(self.runs_ms) if self.runs_ms else 0.0


def _elapsed_ms(output: str) -> float:
    matches = _ELAPSED.findall(output)
    if not matches:
        raise RuntimeError(f"no elapsed time in sqlcmd output:\n{output[:500]}")
    return float(matches[-1])


def _capture_plan(sql: str) -> str:
    out = run_sql_plan(f"SET STATISTICS XML ON;\n{sql}\nSET STATISTICS XML OFF;", DB)
    start = out.find("<ShowPlanXML")
    end = out.rfind("</ShowPlanXML>")
    if start == -1 or end == -1:
        raise RuntimeError(f"no plan XML captured:\n{out[:500]}")
    return out[start : end + len("</ShowPlanXML>")]


def measure(
    sql: str, label: str, runs: int = 5, clear_cache: bool = True
) -> Measurement:
    """Time `sql` and capture its actual plan.

    clear_cache drops both the plan cache and the buffer pool before the
    warm-up, which is the honest comparison for a plan-shape change: it stops
    the second query benefiting from pages the first one loaded.
    """
    timed = f"SET STATISTICS TIME ON;\n{sql}\nSET STATISTICS TIME OFF;"

    if clear_cache:
        run_sql("DBCC FREEPROCCACHE; DBCC DROPCLEANBUFFERS;", DB)
    run_sql_timed(timed, DB)  # warm-up, discarded

    samples = [_elapsed_ms(run_sql_timed(timed, DB)) for _ in range(runs)]
    return Measurement(label=label, runs_ms=samples, plan_xml=_capture_plan(sql))


def measure_pathology(directory: Path) -> dict[str, Measurement]:
    directory = Path(directory)
    keep_cache = (directory / KEEP_CACHE_MARKER).exists()

    setup = directory / "setup.sql"
    if setup.exists():
        run_sql_file(setup)

    results: dict[str, Measurement] = {}
    for variant in ("slow", "fast"):
        sql = (directory / f"{variant}.sql").read_text(encoding="utf-8")
        results[variant] = measure(
            sql,
            label=f"{directory.name}:{variant}",
            clear_cache=not keep_cache,
        )

    plans = REPO_ROOT / "results"
    plans.mkdir(exist_ok=True)
    for variant, m in results.items():
        target = plans / f"{directory.name}-{variant}.sqlplan"
        target.write_text(m.plan_xml, encoding="utf-8")
    return results
