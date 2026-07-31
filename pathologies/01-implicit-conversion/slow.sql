-- N'' makes this literal NVARCHAR. AccountCode is VARCHAR, and NVARCHAR has
-- the higher datatype precedence, so SQL Server converts the COLUMN rather
-- than the literal. A converted column is not SARGable, so
-- IX_Customers_AccountCode can only be scanned.
SELECT CustomerId, DisplayName
FROM dbo.Customers
WHERE AccountCode = N'ACCT-00042000';
