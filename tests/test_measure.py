import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.measure import Measurement, measure


def test_measure_returns_plan_and_runs():
    m = measure("SELECT COUNT(*) FROM dbo.Orders;", label="count", runs=3)

    assert isinstance(m, Measurement)
    assert m.label == "count"
    assert len(m.runs_ms) == 3
    assert m.median_ms > 0
    assert m.logical_reads > 0
    assert "<ShowPlanXML" in m.plan_xml


def test_median_is_the_middle_not_the_mean():
    m = Measurement(label="x", runs_ms=[1.0, 2.0, 100.0], logical_reads=0, plan_xml="")
    assert m.median_ms == 2.0
