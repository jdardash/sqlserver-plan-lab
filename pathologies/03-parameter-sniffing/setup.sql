-- Compile the procedure for the atypical customer, then leave that plan
-- cached. Every later call reuses a plan built for a third of the table.
CREATE OR ALTER PROCEDURE dbo.GetOrdersByCustomer
    @CustomerId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderId, OrderDate, Status, AmountMinor, Notes
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId;
END;
GO

DBCC FREEPROCCACHE;
GO

-- Prime the cache with the skewed value. CustomerId 1 owns 666,693 of the two
-- million rows, so the optimiser picks a scan and caches it.
EXEC dbo.GetOrdersByCustomer @CustomerId = 1;
GO
