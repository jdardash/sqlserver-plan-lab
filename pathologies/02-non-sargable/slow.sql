-- Formatting the column to a string and comparing strings. This is genuinely
-- non-SARGable: IX_Orders_OrderDate is ordered by OrderDate, not by its
-- rendered text, so there is no contiguous range to seek and all two million
-- rows are converted and compared.
--
-- Note this is deliberately NOT the CAST(OrderDate AS DATE) example that most
-- write-ups use. SQL Server has special-cased casting a date-typed column to
-- DATE since 2008: the optimiser rewrites it into a range seek, so it is
-- SARGable and demonstrates nothing. Measured at 1.0x here before the example
-- was corrected.
SELECT COUNT(*) AS order_count, SUM(AmountMinor) AS total_minor
FROM dbo.Orders
WHERE CONVERT(VARCHAR(10), OrderDate, 120) = '2023-06-15';
