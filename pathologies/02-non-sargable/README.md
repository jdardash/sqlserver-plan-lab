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

## What the captured plan shows

Extracted from the committed captures
([slow](../../results/02-non-sargable-slow.sqlplan),
[fast](../../results/02-non-sargable-fast.sqlplan)) by
`python -m lab plans`, and regenerated on every run. Open the `.sqlplan` files
in SSMS for the full picture.

<!-- PLAN:START -->

| Variant | Operator | Rows read | Rows returned | Executions |
| --- | --- | ---: | ---: | ---: |
| slow | Clustered Index Scan of `Orders.PK_Orders` | 2,000,000 | 1,440 | 16 |
| fast | Index Seek of `Orders.IX_Orders_OrderDate` | 1,440 | 1,440 | 1 |
| fast | Clustered Index Seek of `Orders.PK_Orders` | 1,440 | 1,440 | 1,440 |

Optimizer warning in the slow plan: `Cardinality Estimate: CONVERT(varchar(10),[PlanLab].[dbo].[Orders].[OrderDate],120)`

Optimizer warning in the slow plan: `Seek Plan: CONVERT(varchar(10),[PlanLab].[dbo].[Orders].[OrderDate],120)=[@1]`

Optimizer warning in the slow plan: `Seek Plan: CONVERT(varchar(10),[PlanLab].[dbo].[Orders].[OrderDate],120)='2023-06-15'`

<!-- PLAN:END -->
