"""Capture actual execution plans, logical reads, and elapsed time.

Logical reads are the primary metric here, not milliseconds. That is a
deliberate choice and it is the one a DBA would make:

* Logical reads are deterministic. The same plan against the same data reads
  the same number of pages on your laptop and on a CI runner.
* Milliseconds are not. They move with cache state, CPU contention, and what
  else the machine is doing.
* Resolution. A warm single-row index seek finishes in well under a
  microsecond, below what SYSUTCDATETIME can resolve, so it times as zero. The
  same seek reads a stable 3 pages against a scan's 5,000-plus, and that ratio
  is the real story.

Elapsed time is still reported, as a median of N runs after a discarded
warm-up, because it is what anyone actually feels. It is context, not proof.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from lab.sqlcmd import run_sql, run_sql_file, run_sql_io, run_sql_plan, run_sql_timed

DB = "PlanLab"
REPO_ROOT = Path(__file__).resolve().parent.parent

_ELAPSED = re.compile(r"LABTIME=(\d+)")
_LOGICAL_READS = re.compile(r"logical reads (\d+)", re.IGNORECASE)

# SYSUTCDATETIME on DATETIME2(7) resolves to 100 nanoseconds, which is finer
# than SET STATISTICS TIME's whole milliseconds. It is still not fine enough
# for a warm seek, which is why logical reads carry the argument.
_TIMED_BATCH = """\
DECLARE @lab_t0 DATETIME2(7) = SYSUTCDATETIME();
{sql}
SELECT CONCAT('LABTIME=', DATEDIFF(MICROSECOND, @lab_t0, SYSUTCDATETIME()));
"""

# Presence of this file means the pathology depends on a warm plan cache and
# clearing it would destroy the effect being demonstrated.
KEEP_CACHE_MARKER = "KEEP_PLAN_CACHE"


@dataclass
class Measurement:
    label: str
    runs_ms: list[float]
    logical_reads: int
    plan_xml: str

    @property
    def median_ms(self) -> float:
        return statistics.median(self.runs_ms) if self.runs_ms else 0.0


def _elapsed_ms(output: str) -> float:
    matches = _ELAPSED.findall(output)
    if not matches:
        raise RuntimeError(f"no elapsed time in sqlcmd output:\n{output[:500]}")
    return float(matches[-1]) / 1000.0


def _logical_reads(sql: str) -> int:
    """Total pages read across every table the statement touched."""
    out = run_sql_io(f"SET STATISTICS IO ON;\n{sql}\nSET STATISTICS IO OFF;", DB)
    matches = _LOGICAL_READS.findall(out)
    if not matches:
        raise RuntimeError(f"no logical reads in sqlcmd output:\n{out[:500]}")
    return sum(int(m) for m in matches)


def _capture_plan(sql: str) -> str:
    out = run_sql_plan(f"SET STATISTICS XML ON;\n{sql}\nSET STATISTICS XML OFF;", DB)
    start = out.find("<ShowPlanXML")
    end = out.rfind("</ShowPlanXML>")
    if start == -1 or end == -1:
        raise RuntimeError(f"no plan XML captured:\n{out[:500]}")
    return out[start : end + len("</ShowPlanXML>")]


def measure(
    sql: str,
    label: str,
    runs: int = 5,
    clear_cache: bool = True,
    setup: Path | None = None,
) -> Measurement:
    """Time `sql`, count its logical reads, and capture its actual plan.

    clear_cache drops both the plan cache and the buffer pool before the
    warm-up, which is the honest comparison for a plan-shape change: without
    it the second variant benefits from pages the first one already loaded.

    `setup` is re-run before each of the three measurement phases. That matters
    for cache-dependent pathologies: SET STATISTICS IO and SET STATISTICS XML
    change the SET options, which changes the plan cache key and forces a
    recompile. Without re-priming, the recompile would sniff the parameter
    actually being measured and the pathology would silently stop reproducing
    for the reads and plan phases while still looking fine in the timings.
    """
    statement = sql.rstrip().rstrip(";") + ";"
    timed = _TIMED_BATCH.format(sql=statement)

    def prime() -> None:
        if setup is not None:
            run_sql_file(setup)

    if clear_cache:
        run_sql("DBCC FREEPROCCACHE; DBCC DROPCLEANBUFFERS;", DB)
    prime()
    run_sql_timed(timed, DB)  # warm-up, discarded
    samples = [_elapsed_ms(run_sql_timed(timed, DB)) for _ in range(runs)]

    prime()
    reads = _logical_reads(statement)

    prime()
    plan = _capture_plan(statement)

    return Measurement(
        label=label, runs_ms=samples, logical_reads=reads, plan_xml=plan
    )


# Indexes that individual pathologies create. They are dropped before every
# pathology so results do not depend on execution order.
#
# This is not hypothetical tidiness: pathology 04's covering index survived into
# pathology 02 and gave its scan a narrower structure to read, moving 02 from
# 44,447 logical reads to 10,202 depending only on which ran first.
OPTIONAL_INDEXES = (
    "IX_Orders_Status_OrderDate_Covering",
    "IX_Orders_OrderDate_Narrow",
)


def reset_indexes() -> None:
    statements = "\n".join(
        f"DROP INDEX IF EXISTS {name} ON dbo.Orders;" for name in OPTIONAL_INDEXES
    )
    run_sql(statements, DB)


def measure_pathology(directory: Path) -> dict[str, Measurement]:
    directory = Path(directory)
    keep_cache = (directory / KEEP_CACHE_MARKER).exists()

    reset_indexes()

    setup = directory / "setup.sql"
    if setup.exists():
        run_sql_file(setup)
    else:
        setup = None

    results: dict[str, Measurement] = {}
    for variant in ("slow", "fast"):
        # Per-variant setup exists so DDL never sits inside the timed
        # statement. Pathology 04 differs only by an index; creating that index
        # inside fast.sql would both fail on the second of six runs and charge
        # the build time to the query being measured.
        variant_setup = directory / f"{variant}_setup.sql"
        if variant_setup.exists():
            run_sql_file(variant_setup)

        sql = (directory / f"{variant}.sql").read_text(encoding="utf-8")
        results[variant] = measure(
            sql,
            label=f"{directory.name}:{variant}",
            clear_cache=not keep_cache,
            # Only cache-dependent pathologies need re-priming between phases.
            setup=setup if keep_cache else None,
        )

    plans = REPO_ROOT / "results"
    plans.mkdir(exist_ok=True)
    for variant, m in results.items():
        target = plans / f"{directory.name}-{variant}.sqlplan"
        target.write_text(m.plan_xml, encoding="utf-8")
    return results
