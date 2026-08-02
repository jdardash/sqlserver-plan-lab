"""Read the story out of a captured showplan and write it into the README.

The .sqlplan files in results/ are the evidence for every claim in this
repository, but they are only evidence to someone who opens them in SSMS. This
module extracts the part that carries each argument - which operators touched
data, how many rows they read against how many they returned, how many times
they executed, and what the optimizer warned about - and regenerates a table
in each pathology's README from it. Same rule as the results table: nothing
hand-typed, so the prose can never quietly drift from the capture.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

NS = "{http://schemas.microsoft.com/sqlserver/2004/07/showplan}"

START = "<!-- PLAN:START -->"
END = "<!-- PLAN:END -->"


@dataclass
class Operator:
    """A data-access operator: a RelOp that names a table or index."""

    physical: str
    object_name: str
    actual_rows: int
    executions: int
    # Rows the storage engine handed the operator before any residual
    # predicate, when the plan records it. A wide gap between rows_read and
    # actual_rows is the signature of a predicate applied too late.
    rows_read: int | None


@dataclass
class PlanSummary:
    data_ops: list[Operator] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _object_name(obj: ET.Element) -> str:
    table = obj.get("Table", "").strip("[]")
    index = obj.get("Index", "").strip("[]")
    return f"{table}.{index}" if index else table


def _counter_sum(relop: ET.Element, attr: str) -> int | None:
    threads = relop.findall(f"./{NS}RunTimeInformation/{NS}RunTimeCountersPerThread")
    values = [t.get(attr) for t in threads]
    if not any(v is not None for v in values):
        return None
    return sum(int(v) for v in values if v is not None)


def parse_plan(path: Path) -> PlanSummary:
    text = Path(path).read_text(encoding="utf-8")
    # Showplan XML never carries a DTD, and both XXE and entity-expansion
    # attacks require one. Refusing DTDs outright closes the stdlib parser's
    # known holes without pulling in defusedxml for files this repo generates.
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise RuntimeError(f"refusing to parse {path}: showplan XML has no DTD")
    root = ET.fromstring(text)
    summary = PlanSummary()

    for relop in root.iter(f"{NS}RelOp"):
        # The operator-specific element (IndexScan, IndexSeek, ...) is a direct
        # child of RelOp, so its Object is a grandchild. Objects belonging to
        # nested operators sit deeper and are not picked up here.
        objects = relop.findall(f"./{NS}*/{NS}Object")
        if not objects:
            continue
        summary.data_ops.append(
            Operator(
                physical=relop.get("PhysicalOp", "?"),
                object_name=_object_name(objects[0]),
                actual_rows=_counter_sum(relop, "ActualRows") or 0,
                executions=_counter_sum(relop, "ActualExecutions") or 0,
                rows_read=_counter_sum(relop, "ActualRowsRead"),
            )
        )

    for warn in root.iter(f"{NS}PlanAffectingConvert"):
        text = f"{warn.get('ConvertIssue')}: {warn.get('Expression')}"
        if text not in summary.warnings:
            summary.warnings.append(text)

    return summary


def _fmt(value: int | None) -> str:
    return f"{value:,}" if value is not None else "-"


def render_section(slow: PlanSummary, fast: PlanSummary) -> str:
    lines = [
        "| Variant | Operator | Rows read | Rows returned | Executions |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for variant, plan in (("slow", slow), ("fast", fast)):
        for op in plan.data_ops:
            lines.append(
                f"| {variant} | {op.physical} of `{op.object_name}` "
                f"| {_fmt(op.rows_read)} | {_fmt(op.actual_rows)} "
                f"| {_fmt(op.executions)} |"
            )
    for variant, plan in (("slow", slow), ("fast", fast)):
        for warning in plan.warnings:
            lines.append("")
            lines.append(f"Optimizer warning in the {variant} plan: `{warning}`")
    return "\n".join(lines) + "\n"


def write_section(section: str, readme: Path) -> None:
    readme = Path(readme)
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"plan markers missing from {readme}")
    readme.write_text(
        pattern.sub(f"{START}\n\n{section}\n{END}", text), encoding="utf-8"
    )


def generate_all(repo_root: Path) -> list[str]:
    """Regenerate the plan section of every pathology README from results/.

    Reads only committed captures, so it runs without Docker or a database.
    Returns the pathology names it updated.
    """
    repo_root = Path(repo_root)
    updated = []
    for directory in sorted((repo_root / "pathologies").iterdir()):
        if not directory.is_dir():
            continue
        slow = repo_root / "results" / f"{directory.name}-slow.sqlplan"
        fast = repo_root / "results" / f"{directory.name}-fast.sqlplan"
        if not slow.exists() or not fast.exists():
            raise RuntimeError(f"missing plan capture for {directory.name}")
        section = render_section(parse_plan(slow), parse_plan(fast))
        write_section(section, directory / "README.md")
        updated.append(directory.name)
    return updated
