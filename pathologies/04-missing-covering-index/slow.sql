-- No index leads on Status, so there is no access path more selective than
-- reading the whole table.
SELECT COUNT(*) AS order_count, SUM(AmountMinor) AS total_minor
FROM dbo.Orders
WHERE Status = 'CANCELLED'
  AND OrderDate >= '2023-01-01' AND OrderDate < '2024-01-01';
