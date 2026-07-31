-- FORCESEEK makes the optimiser take the seek it correctly rejected. Roughly
-- half a million qualifying rows each cost a Key Lookup to fetch Notes.
SELECT OrderId, OrderDate, Notes
FROM dbo.Orders WITH (FORCESEEK, INDEX(IX_Orders_OrderDate_Narrow))
WHERE OrderDate >= '2023-01-01' AND OrderDate < '2024-01-01';
