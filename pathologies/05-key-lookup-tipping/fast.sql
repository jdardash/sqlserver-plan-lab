-- Identical rows, no hint. Above the tipping point the optimiser prefers one
-- sequential scan to half a million random lookups, and it is right.
SELECT OrderId, OrderDate, Notes
FROM dbo.Orders
WHERE OrderDate >= '2023-01-01' AND OrderDate < '2024-01-01';
