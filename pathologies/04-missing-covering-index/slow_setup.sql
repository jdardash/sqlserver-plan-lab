-- Guarantee the covering index is absent, whatever ran before this.
DROP INDEX IF EXISTS IX_Orders_Status_OrderDate_Covering ON dbo.Orders;
GO
