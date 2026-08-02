"""Lab CLI: python -m lab seed | run | plans"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.sqlcmd import run_sql_file

REPO_ROOT = Path(__file__).resolve().parent.parent

# A pathology that does not cut logical reads by at least this factor has
# stopped reproducing, and the repository should fail loudly rather than
# publish a table of ones.
#
# The gate is on logical reads, not elapsed time. Time is unusable as a gate
# here: a warm index seek finishes below the timer's resolution and reports
# zero, so a time-based gate divides by zero and calls the best results in the
# table failures. It did exactly that before this was fixed.
MIN_READ_REDUCTION = 2.0


def seed() -> int:
    run_sql_file(REPO_ROOT / "schema" / "01_schema.sql", database="master")
    print(run_sql_file(REPO_ROOT / "schema" / "02_seed.sql"))
    return 0


def plans() -> int:
    """Regenerate every pathology README's plan section from results/.

    Works offline: it reads the committed captures, not the database.
    """
    from lab.plans import generate_all

    for name in generate_all(REPO_ROOT):
        print(f"plan section regenerated for {name}")
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
    plans()
    print()
    print(table)

    failed = [
        name
        for name, r in results.items()
        if r["slow"].logical_reads / max(r["fast"].logical_reads, 1)
        < MIN_READ_REDUCTION
    ]
    if failed:
        print(f"pathologies failed to reproduce: {', '.join(failed)}")
        return 1
    print("all pathologies reproduced")
    return 0


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else ""
    if command == "seed":
        return seed()
    if command == "run":
        return run()
    if command == "plans":
        return plans()
    print("usage: python -m lab seed | run | plans", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
