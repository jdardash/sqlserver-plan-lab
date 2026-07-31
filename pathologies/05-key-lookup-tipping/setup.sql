-- A narrow index on OrderDate exists and does not cover Notes, so every
-- qualifying row costs one lookup into the clustered index.
DROP INDEX IF EXISTS IX_Orders_OrderDate_Narrow ON dbo.Orders;
GO
CREATE INDEX IX_Orders_OrderDate_Narrow ON dbo.Orders (OrderDate);
GO
