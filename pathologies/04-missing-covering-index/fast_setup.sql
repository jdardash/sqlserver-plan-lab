-- The only difference between the slow and fast variants of this pathology.
-- The query text is byte-identical; this index is what changes the plan.
--
-- Equality column first, range column second. Reversing that key order leaves
-- the seek unable to use OrderDate. AmountMinor is INCLUDEd rather than keyed
-- because it is fetched, never searched: keying it would widen every level of
-- the b-tree, whereas including it adds it to the leaf pages only.
DROP INDEX IF EXISTS IX_Orders_Status_OrderDate_Covering ON dbo.Orders;
GO
CREATE INDEX IX_Orders_Status_OrderDate_Covering
    ON dbo.Orders (Status, OrderDate)
    INCLUDE (AmountMinor);
GO
