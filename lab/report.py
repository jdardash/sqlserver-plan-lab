"""Regenerate the README results table from measured data.

Nothing in the table is hand-typed. If a pathology stops reproducing, the next
run says so in the README and the build fails. A hand-written performance table
is unfalsifiable, which is the opposite of what this repository is for.
"""

from __future__ import annotations

import re
from pathlib import Path

from lab.measure import Measurement

START = "<!-- RESULTS:START -->"
END = "<!-- RESULTS:END -->"

HEADER = (
    "| Pathology | Logical reads | Reads saved | Median time | Runs |\n"
    "| --- | ---: | ---: | ---: | ---: |\n"
)


def _fmt_ms(value: float) -> str:
    if value == 0:
        return "under 0.01 ms"
    if value < 10:
        return f"{value:.2f} ms"
    return f"{value:.0f} ms"


def render_table(results: dict[str, dict[str, Measurement]]) -> str:
    rows = [HEADER]
    for name in sorted(results):
        slow = results[name]["slow"]
        fast = results[name]["fast"]
        ratio = slow.logical_reads / max(fast.logical_reads, 1)
        rows.append(
            f"| `{name}` "
            f"| {slow.logical_reads:,} to {fast.logical_reads:,} "
            f"| {ratio:.0f}x "
            f"| {_fmt_ms(slow.median_ms)} to {_fmt_ms(fast.median_ms)} "
            f"| {len(slow.runs_ms)} |\n"
        )
    return "".join(rows)


def write_readme(table: str, readme: Path) -> None:
    readme = Path(readme)
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"results markers missing from {readme}")
    readme.write_text(
        pattern.sub(f"{START}\n\n{table}\n{END}", text), encoding="utf-8"
    )
