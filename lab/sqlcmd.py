"""Run SQL inside the lab container.

Everything goes through `docker exec`, so reproducing this repository needs
Docker and nothing else: no local ODBC driver, no connection string, no
platform-specific client install. That constraint is deliberate. A performance
claim nobody can reproduce is not evidence.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

CONTAINER = "planlab-mssql"
SQLCMD = "/opt/mssql-tools18/bin/sqlcmd"
PASSWORD = "PlanLab!Passw0rd"


class SqlcmdError(RuntimeError):
    """sqlcmd exited non-zero. Carries the server's own message."""


def _exec(args: list[str], stdin: str | None = None) -> str:
    proc = subprocess.run(
        [
            "docker", "exec", "-i", CONTAINER, SQLCMD,
            # -C trusts the container's self-signed certificate.
            # -b makes sqlcmd exit non-zero on a SQL error, so a broken
            #    pathology fails the build instead of reporting 0 ms.
            "-C", "-S", "localhost", "-U", "sa", "-P", PASSWORD, "-b",
            *args,
        ],
        input=stdin,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SqlcmdError((proc.stderr or proc.stdout).strip())
    return proc.stdout


def run_sql(sql: str, database: str = "master") -> str:
    return _exec(["-d", database, "-Q", sql])


def run_sql_file(path: Path, database: str = "PlanLab") -> str:
    return _exec(["-d", database], stdin=Path(path).read_text(encoding="utf-8"))
