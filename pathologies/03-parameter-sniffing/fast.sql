-- OPTIMIZE FOR UNKNOWN plans against the column's average density instead of
-- the sniffed outlier, so a typical customer gets the seek it deserves.
DECLARE @CustomerId INT = 27;
SELECT OrderId, OrderDate, Status, AmountMinor, Notes
FROM dbo.Orders
WHERE CustomerId = @CustomerId
OPTION (OPTIMIZE FOR UNKNOWN);
