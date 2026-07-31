-- Identical rows, expressed as a half-open range so the column stays bare and
-- the index seeks straight to the 1,440 rows that qualify.
--
-- Half-open rather than BETWEEN on purpose: BETWEEN '2023-06-15' AND
-- '2023-06-15 23:59:59' silently drops the final second, which is a
-- correctness bug hiding inside a performance fix.
SELECT COUNT(*) AS order_count, SUM(AmountMinor) AS total_minor
FROM dbo.Orders
WHERE OrderDate >= '2023-06-15' AND OrderDate < '2023-06-16';
