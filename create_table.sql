
--
USE WAREHOUSE TEACH_WH;          -- choose the compute engine
USE DATABASE RETAIL_LAB;         -- choose where data lives
USE SCHEMA STG;                  -- choose sub-folder in database

CREATE TABLE IF NOT EXISTS RETAIL_LAB.DWH.SALES (
    ORDER_ID      NUMBER,
    CUSTOMER_ID   NUMBER,
    PRODUCT_ID    NUMBER,
    QUANTITY      NUMBER,
    UNIT_PRICE    NUMBER(10,2),
    ORDER_TOTAL   NUMBER(12,2),
    SOLD_AT       TIMESTAMP_NTZ,
    _INGESTED_AT  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);