# 02. Non-SARGable predicate

**Symptom.** A single-day filter on an indexed date column reads the entire
table.

**Cause.** `CONVERT(VARCHAR(10), OrderDate, 120)` renders the column to text
and compares strings. The index is ordered by `OrderDate`, not by its rendered
text, so there is no contiguous range to seek and all two million rows are
converted and compared.

**Fix.** A half-open range, `>= start AND < next_start`. Half-open rather than
`BETWEEN`: `BETWEEN '2023-06-15' AND '2023-06-15 23:59:59'` silently drops the
final second, which is a correctness bug hiding inside a performance fix.

**Why this example and not the usual one.** Most write-ups demonstrate this
with `CAST(OrderDate AS DATE) = '...'`. That is wrong. SQL Server has
special-cased casting a date-typed column to `DATE` since 2008: the optimiser
rewrites it into a range seek, so it is SARGable and demonstrates nothing. It
was measured here at 1.0x before the example was corrected. Wrapping a column
in a function usually breaks the seek, but "usually" is not "always", and the
plan is what settles it.
