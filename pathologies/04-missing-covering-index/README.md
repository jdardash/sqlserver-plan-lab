# 04. Missing covering index

**Symptom.** A narrow aggregate over a small slice of a large table takes as
long as reading the whole table, because it is reading the whole table.

**Cause.** No index leads on `Status`, so no access path is more selective
than a full scan.

**Note on the files.** `slow.sql` and `fast.sql` are byte-identical. The only
difference is `fast_setup.sql`, which creates the covering index. Index
creation is kept out of the timed statement deliberately: DDL inside a measured
query would charge the index build to the query.

**Fix.** An index keyed on the equality column first and the range column
second, with the aggregated column in `INCLUDE`. Key order matters. Reversing
it leaves the seek unable to use the second column.

**Why INCLUDE rather than a third key column.** `AmountMinor` is fetched, never
searched. Keying it would widen every level of the b-tree; including it adds it
to the leaf pages only.

**Cost, stated honestly.** This index is not free. It adds write cost to every
insert and update on `dbo.Orders` and it consumes storage. Covering indexes are
a trade, not a win, and anyone presenting them as free has not measured the
write side.

## What the captured plan shows

Extracted from the committed captures
([slow](../../results/04-missing-covering-index-slow.sqlplan),
[fast](../../results/04-missing-covering-index-fast.sqlplan)) by
`python -m lab plans`, and regenerated on every run. Open the `.sqlplan` files
in SSMS for the full picture.

<!-- PLAN:START -->

| Variant | Operator | Rows read | Rows returned | Executions |
| --- | --- | ---: | ---: | ---: |
| slow | Clustered Index Scan of `Orders.PK_Orders` | 2,000,000 | 75,086 | 16 |
| fast | Index Seek of `Orders.IX_Orders_Status_OrderDate_Covering` | 75,086 | 75,086 | 1 |

<!-- PLAN:END -->
