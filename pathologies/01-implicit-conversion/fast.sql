-- Same value, matching datatype. The column stays bare, so the index seeks.
SELECT CustomerId, DisplayName
FROM dbo.Customers
WHERE AccountCode = 'ACCT-00042000';
