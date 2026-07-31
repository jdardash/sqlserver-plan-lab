import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.measure import Measurement
from lab.report import render_table, write_readme


def _results():
    return {
        "01-implicit-conversion": {
            "slow": Measurement(
                label="s", runs_ms=[100.0, 110.0, 120.0],
                logical_reads=3376, plan_xml=""
            ),
            "fast": Measurement(
                label="f", runs_ms=[0.0, 0.0, 0.0],
                logical_reads=6, plan_xml=""
            ),
        }
    }


def test_render_table_reports_reads_and_ratio():
    table = render_table(_results())
    assert "01-implicit-conversion" in table
    assert "3,376 to 6" in table
    assert "563x" in table


def test_sub_resolution_time_is_labelled_not_zero():
    table = render_table(_results())
    assert "under 0.01 ms" in table
    assert "0 ms to 0 ms" not in table


def test_write_readme_replaces_only_between_markers(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "before\n<!-- RESULTS:START -->\nstale\n<!-- RESULTS:END -->\nafter\n",
        encoding="utf-8",
    )
    write_readme("FRESH", readme)
    text = readme.read_text(encoding="utf-8")

    assert "before" in text and "after" in text
    assert "stale" not in text and "FRESH" in text
