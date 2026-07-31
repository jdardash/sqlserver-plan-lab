import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.sqlcmd import SqlcmdError, run_sql


def test_run_sql_returns_output():
    assert "42" in run_sql("SELECT 42 AS answer;")


def test_run_sql_raises_on_bad_sql():
    with pytest.raises(SqlcmdError) as excinfo:
        run_sql("SELECT * FROM table_that_does_not_exist;")
    assert "table_that_does_not_exist" in str(excinfo.value)
