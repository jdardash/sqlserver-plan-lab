"""Run SQL inside the lab container.

Everything goes through `docker exec`, so reproducing this repository needs
Docker and nothing else: no local ODBC driver, no connection string, no
platform-specific client install. That constraint is deliberate. A performance
claim nobody can reproduce is not evidence.

Two details that are not obvious:

* sqlcmd output is written to a file inside the container and filtered there.
  Some pathology queries return half a million rows; pulling those through a
  pipe into Python would dominate the measurement and tell you about the pipe
  rather than the plan.
* Plan capture needs `-y 0`. The default variable-length display width is 256
  characters, which silently truncates showplan XML into unparseable garbage.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

CONTAINER = "planlab-mssql"
SQLCMD = "/opt/mssql-tools18/bin/sqlcmd"
PASSWORD = "PlanLab!Passw0rd"
OUT_FILE = "/tmp/planlab_out.txt"


class SqlcmdError(RuntimeError):
    """sqlcmd exited non-zero. Carries the server's own message."""


def _quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _run(
    database: str,
    *,
    query: str | None = None,
    stdin: str | None = None,
    grep: str | None = None,
    wide: bool = False,
) -> str:
    """Execute SQL in the container, optionally returning only matching lines.

    `grep` is an extended-regex applied inside the container, so large result
    sets never cross the process boundary.
    """
    parts = [
        SQLCMD,
        # -C trusts the container's self-signed certificate.
        # -b exits non-zero on a SQL error, so a broken pathology fails the
        #    build instead of quietly reporting 0 ms.
        "-C", "-S", "localhost", "-U", "sa", "-P", _quote(PASSWORD), "-b",
        "-d", _quote(database),
    ]
    if wide:
        parts += ["-y", "0"]
    if query is not None:
        parts += ["-Q", _quote(query)]
    parts += ["-o", OUT_FILE]

    script = " ".join(parts)
    if grep:
        script += f"; status=$?; grep -aE {_quote(grep)} {OUT_FILE}; exit $status"
    else:
        script += f"; status=$?; cat {OUT_FILE}; exit $status"

    # With no stdin payload, hand the child DEVNULL instead of inheriting the
    # parent's stdin. Inheriting fails with WinError 6 wherever the parent has
    # no valid stdin handle (headless runners, service contexts), and this
    # harness never wants the child reading an interactive terminal anyway.
    io = {"input": stdin} if stdin is not None else {"stdin": subprocess.DEVNULL}
    proc = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "sh", "-c", script],
        capture_output=True,
        text=True,
        **io,
    )
    if proc.returncode != 0:
        raise SqlcmdError((proc.stdout or proc.stderr).strip())
    return proc.stdout


def run_sql(sql: str, database: str = "master") -> str:
    return _run(database, query=sql)


def run_sql_file(path: Path, database: str = "PlanLab") -> str:
    return _run(database, stdin=Path(path).read_text(encoding="utf-8"))


def run_sql_timed(sql: str, database: str = "PlanLab") -> str:
    """Run `sql` and return only the harness timing marker line."""
    return _run(database, query=sql, grep="LABTIME=")


def run_sql_io(sql: str, database: str = "PlanLab") -> str:
    """Run `sql` under SET STATISTICS IO and return only the page-count lines."""
    return _run(database, query=sql, grep="logical reads")


def run_sql_plan(sql: str, database: str = "PlanLab") -> str:
    """Run `sql` under SET STATISTICS XML and return only the plan XML lines."""
    return _run(database, query=sql, grep="ShowPlanXML", wide=True)
