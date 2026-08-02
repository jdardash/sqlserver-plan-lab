IF DB_ID('PlanLab') IS NULL
BEGIN
    CREATE DATABASE PlanLab;
END;
GO

USE PlanLab;
GO

DROP TABLE IF EXISTS dbo.Orders;
DROP TABLE IF EXISTS dbo.Customers;
GO

-- Primary keys are named. An unnamed PK gets a system-generated name with a
-- random suffix (PK__Orders__C3905BCF4B981A07), different on every seed, which
-- makes plans from two environments needlessly hard to diff and leaks into the
-- generated plan tables in the pathology READMEs.
CREATE TABLE dbo.Customers (
    CustomerId   INT            NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    -- Deliberately VARCHAR. Pathology 01 compares it to an NVARCHAR literal
    -- and the datatype precedence rules convert the column, not the literal.
    AccountCode  VARCHAR(20)    NOT NULL,
    DisplayName  NVARCHAR(120)  NOT NULL,
    Region       VARCHAR(10)    NOT NULL
);
GO

CREATE TABLE dbo.Orders (
    OrderId      BIGINT         NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId   INT            NOT NULL,
    OrderDate    DATETIME2(3)   NOT NULL,
    Status       VARCHAR(12)    NOT NULL,
    AmountMinor  BIGINT         NOT NULL,
    -- Wide on purpose. A key lookup has to fetch something expensive before
    -- the tipping point in pathology 05 is measurable.
    Notes        NVARCHAR(200)  NOT NULL
);
GO

CREATE INDEX IX_Customers_AccountCode ON dbo.Customers (AccountCode);
CREATE INDEX IX_Orders_CustomerId     ON dbo.Orders (CustomerId);
CREATE INDEX IX_Orders_OrderDate      ON dbo.Orders (OrderDate);
GO
