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
