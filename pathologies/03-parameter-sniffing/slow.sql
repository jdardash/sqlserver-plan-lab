-- A typical customer owns 27 rows, but inherits the scan plan cached for
-- CustomerId 1, which owns 666,693.
EXEC dbo.GetOrdersByCustomer @CustomerId = 27;
