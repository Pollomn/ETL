-- Create tables for dropshipping pipeline
-- This script is idempotent and can be run multiple times safely

-- Set context
USE WAREHOUSE mon_entrepot;
USE DATABASE ma_base;

-- Raw events table (from Kafka consumer)
CREATE TABLE IF NOT EXISTS mon_schema.orders_events (
    event_id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    payload VARIANT NOT NULL,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw order events from Kafka';

-- Production tables

-- Customers table
CREATE TABLE IF NOT EXISTS mon_schema.customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    channel VARCHAR(50),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Customer master data';

-- Inventory table
CREATE TABLE IF NOT EXISTS mon_schema.inventory (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Product inventory data';

-- Orders table
CREATE TABLE IF NOT EXISTS mon_schema.orders (
    order_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    sold_at TIMESTAMP_NTZ NOT NULL,
    ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (product_id) REFERENCES mon_schema.inventory(product_id),
    FOREIGN KEY (customer_id) REFERENCES mon_schema.customers(customer_id)
)
COMMENT = 'Order transactions';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_sold_at ON mon_schema.orders(sold_at);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON mon_schema.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON mon_schema.orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_ingested_at ON mon_schema.orders(ingested_at);

-- Show created tables
SHOW TABLES IN SCHEMA mon_schema;
