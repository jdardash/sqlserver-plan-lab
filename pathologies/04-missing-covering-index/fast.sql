-- Byte-identical to slow.sql. See fast_setup.sql: the covering index is the
-- entire difference.
SELECT COUNT(*) AS order_count, SUM(AmountMinor) AS total_minor
FROM dbo.Orders
WHERE Status = 'CANCELLED'
  AND OrderDate >= '2023-01-01' AND OrderDate < '2024-01-01';
