-- Deterministic seed. Every run produces byte-identical data, so a timing
-- delta measured on one machine means the same thing on another.
USE PlanLab;
GO

SET NOCOUNT ON;
GO

;WITH n0 AS (SELECT 1 AS c UNION ALL SELECT 1),
      n1 AS (SELECT 1 AS c FROM n0 a CROSS JOIN n0 b),
      n2 AS (SELECT 1 AS c FROM n1 a CROSS JOIN n1 b),
      n3 AS (SELECT 1 AS c FROM n2 a CROSS JOIN n2 b),
      n4 AS (SELECT 1 AS c FROM n3 a CROSS JOIN n3 b),
      nums AS (SELECT TOP (50000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
               FROM n4 a CROSS JOIN n4 b)
INSERT INTO dbo.Customers (CustomerId, AccountCode, DisplayName, Region)
SELECT i,
       'ACCT-' + RIGHT('00000000' + CAST(i AS VARCHAR(8)), 8),
       N'Customer ' + CAST(i AS NVARCHAR(10)),
       CASE i % 4 WHEN 0 THEN 'WEST' WHEN 1 THEN 'EAST'
                  WHEN 2 THEN 'NORTH' ELSE 'SOUTH' END
FROM nums;
GO

-- Two million orders.
--
-- The skew is the point: CustomerId 1 owns one row in three, while a typical
-- customer owns about forty. Pathology 03 needs that gap, because parameter
-- sniffing is only visible when one parameter value is wildly unrepresentative
-- of the rest.
--
-- Dates span four years at one-minute resolution so a single-year predicate
-- selects a meaningful fraction rather than everything or nothing.
;WITH n0 AS (SELECT 1 AS c UNION ALL SELECT 1),
      n1 AS (SELECT 1 AS c FROM n0 a CROSS JOIN n0 b),
      n2 AS (SELECT 1 AS c FROM n1 a CROSS JOIN n1 b),
      n3 AS (SELECT 1 AS c FROM n2 a CROSS JOIN n2 b),
      n4 AS (SELECT 1 AS c FROM n3 a CROSS JOIN n3 b),
      n5 AS (SELECT 1 AS c FROM n4 a CROSS JOIN n4 b),
      nums AS (SELECT TOP (2000000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
               FROM n5 a CROSS JOIN n5 b)
INSERT INTO dbo.Orders (OrderId, CustomerId, OrderDate, Status, AmountMinor, Notes)
SELECT i,
       CASE WHEN i % 3 = 0 THEN 1 ELSE (i % 50000) + 1 END,
       DATEADD(MINUTE, i % 2103840, '2022-01-01T00:00:00'),
       CASE i % 7 WHEN 0 THEN 'CANCELLED' WHEN 1 THEN 'PENDING' ELSE 'SETTLED' END,
       (i % 250000) + 100,
       N'order note padding to make a key lookup worth measuring ' + CAST(i AS NVARCHAR(10))
FROM nums;
GO

-- FULLSCAN so the optimiser's row estimates are exact. Sampled statistics
-- would make plan choice depend on the sample, and the pathologies would stop
-- reproducing reliably.
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;
UPDATE STATISTICS dbo.Customers WITH FULLSCAN;
GO

SELECT 'Customers' AS table_name, COUNT(*) AS row_count FROM dbo.Customers
UNION ALL
SELECT 'Orders', COUNT(*) FROM dbo.Orders;
GO
