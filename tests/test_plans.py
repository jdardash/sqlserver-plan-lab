"""Tests for the showplan analyzer, run against the committed plan captures.

The fixtures are the real .sqlplan files in results/, not synthetic XML. If a
regenerated capture stops containing the operator story a pathology claims
(the scan, the conversion warning, the per-row lookups), these tests fail,
which is exactly the moment the prose in that pathology's README went stale.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.plans import PlanSummary, parse_plan, render_section, write_section

RESULTS = Path(__file__).resolve().parent.parent / "results"


def _load(name: str) -> PlanSummary:
    return parse_plan(RESULTS / f"{name}.sqlplan")


def test_implicit_conversion_slow_scans_and_warns():
    plan = _load("01-implicit-conversion-slow")
    ops = [op.physical for op in plan.data_ops]
    assert "Index Scan" in ops
    assert any("CONVERT_IMPLICIT" in w for w in plan.warnings)


def test_implicit_conversion_fast_seeks_without_warning():
    plan = _load("01-implicit-conversion-fast")
    assert plan.data_ops[0].physical == "Index Seek"
    assert not any("CONVERT_IMPLICIT" in w for w in plan.warnings)


def test_scan_reports_rows_read_versus_returned():
    scan = _load("01-implicit-conversion-slow").data_ops[0]
    assert scan.rows_read == 1_000_000
    assert scan.actual_rows == 1


def test_key_lookup_shows_per_row_executions():
    plan = _load("05-key-lookup-tipping-slow")
    lookup = next(
        op for op in plan.data_ops if op.physical == "Clustered Index Seek"
    )
    assert lookup.executions > 100_000


def test_operator_names_its_index():
    seek = _load("01-implicit-conversion-fast").data_ops[0]
    assert seek.object_name == "Customers.IX_Customers_AccountCode"


def test_render_section_is_a_markdown_table():
    slow = _load("01-implicit-conversion-slow")
    fast = _load("01-implicit-conversion-fast")
    section = render_section(slow, fast)
    assert section.startswith("|")
    assert "Index Scan" in section and "Index Seek" in section
    assert "1,000,000" in section


def test_write_section_replaces_only_between_markers(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "before\n<!-- PLAN:START -->\nstale\n<!-- PLAN:END -->\nafter\n",
        encoding="utf-8",
    )
    write_section("FRESH", readme)
    text = readme.read_text(encoding="utf-8")

    assert "before" in text and "after" in text
    assert "stale" not in text and "FRESH" in text
