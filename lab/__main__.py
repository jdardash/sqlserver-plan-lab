"""Lab CLI: python -m lab seed | run"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.sqlcmd import run_sql_file

REPO_ROOT = Path(__file__).resolve().parent.parent

# A pathology that does not move wall-clock time by at least this much has
# stopped reproducing, and the repository should fail loudly rather than
# publish a table of ones.
MIN_SPEEDUP = 1.5


def seed() -> int:
    run_sql_file(REPO_ROOT / "schema" / "01_schema.sql", database="master")
    print(run_sql_file(REPO_ROOT / "schema" / "02_seed.sql"))
    return 0


def run() -> int:
    from lab.measure import measure_pathology
    from lab.report import render_table, write_readme

    results = {}
    for directory in sorted((REPO_ROOT / "pathologies").iterdir()):
        if not directory.is_dir():
            continue
        print(f"measuring {directory.name} ...", flush=True)
        results[directory.name] = measure_pathology(directory)

    table = render_table(results)
    write_readme(table, REPO_ROOT / "README.md")
    print()
    print(table)

    failed = [
        name
        for name, r in results.items()
        if r["fast"].median_ms <= 0
        or r["slow"].median_ms / r["fast"].median_ms < MIN_SPEEDUP
    ]
    if failed:
        print(f"pathologies failed to reproduce: {', '.join(failed)}")
        return 1
    return 0


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else ""
    if command == "seed":
        return seed()
    if command == "run":
        return run()
    print("usage: python -m lab seed | run", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
