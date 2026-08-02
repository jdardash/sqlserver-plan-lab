# 01. Implicit conversion kills an index seek

**Symptom.** A predicate on an indexed column scans instead of seeking, with
nothing in the query text to explain why.

**Cause.** `AccountCode` is `VARCHAR`. The literal is `N'...'`, which is
`NVARCHAR`. `NVARCHAR` has the higher datatype precedence, so SQL Server
converts the *column* rather than the literal. A converted column is not
SARGable, so the index cannot be seeked.

**Fix.** Match the literal's datatype to the column's.

**Spotting it in the wild.** `CONVERT_IMPLICIT` appears in the plan's seek or
scan predicate, and the plan carries a `PlanAffectingConvert` warning. This is
the most common cause of a mysteriously slow parameterised query arriving from
an ORM that sends Unicode string parameters by default, which most of them do.

## What the captured plan shows

Extracted from the committed captures
([slow](../../results/01-implicit-conversion-slow.sqlplan),
[fast](../../results/01-implicit-conversion-fast.sqlplan)) by
`python -m lab plans`, and regenerated on every run. Open the `.sqlplan` files
in SSMS for the full picture.

<!-- PLAN:START -->

| Variant | Operator | Rows read | Rows returned | Executions |
| --- | --- | ---: | ---: | ---: |
| slow | Index Scan of `Customers.IX_Customers_AccountCode` | 1,000,000 | 1 | 1 |
| slow | Clustered Index Seek of `Customers.PK_Customers` | 1 | 1 | 1 |
| fast | Index Seek of `Customers.IX_Customers_AccountCode` | 1 | 1 | 1 |
| fast | Clustered Index Seek of `Customers.PK_Customers` | 1 | 1 | 1 |

Optimizer warning in the slow plan: `Seek Plan: CONVERT_IMPLICIT(nvarchar(20),[PlanLab].[dbo].[Customers].[AccountCode],0)=[@1]`

Optimizer warning in the slow plan: `Seek Plan: CONVERT_IMPLICIT(nvarchar(20),[PlanLab].[dbo].[Customers].[AccountCode],0)=N'ACCT-00042000'`

<!-- PLAN:END -->
