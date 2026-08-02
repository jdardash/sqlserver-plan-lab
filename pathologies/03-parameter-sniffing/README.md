# 03. Parameter sniffing

**Symptom.** A stored procedure is fast for months, then becomes slow after a
restart, a failover, or a statistics update, with no code change.

**Cause.** SQL Server compiles a procedure once, for the first parameter value
it happens to see, and reuses that plan for every later value. Here the cache
is primed with `CustomerId = 1`, which owns 666,693 of the two million rows, so
the optimiser picks a scan. A typical customer owning 27 rows then inherits a
plan built for two thirds of a million.

**Fix shown here.** `OPTION (OPTIMIZE FOR UNKNOWN)`, which plans against the
column's average density rather than the sniffed outlier.

**Fix not shown, and why.** `RECOMPILE` also works and is often better, at the
cost of a compile on every call. Choosing between them depends on call
frequency against degree of skew, which is judgement rather than a rule, and a
lab cannot make that call for your workload.

**Spotting it in the wild.** Compare estimated rows against actual rows in the
plan. An estimate off by orders of magnitude, on a plan that used to be fine,
is the signature.

**Note on measurement.** This is the one pathology whose harness does not clear
the plan cache between runs, because the poisoned cache *is* the pathology. See
`KEEP_PLAN_CACHE` in this directory.

## What the captured plan shows

Extracted from the committed captures
([slow](../../results/03-parameter-sniffing-slow.sqlplan),
[fast](../../results/03-parameter-sniffing-fast.sqlplan)) by
`python -m lab plans`, and regenerated on every run. Open the `.sqlplan` files
in SSMS for the full picture.

<!-- PLAN:START -->

| Variant | Operator | Rows read | Rows returned | Executions |
| --- | --- | ---: | ---: | ---: |
| slow | Clustered Index Scan of `Orders.PK_Orders` | 2,000,000 | 27 | 16 |
| fast | Index Seek of `Orders.IX_Orders_CustomerId` | 27 | 27 | 1 |
| fast | Clustered Index Seek of `Orders.PK_Orders` | 27 | 27 | 27 |

<!-- PLAN:END -->
