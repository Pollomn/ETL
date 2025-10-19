-- Validation queries for data ingestion
-- Run these queries to verify data quality and completeness

-- Set context
USE WAREHOUSE COMPUTE_WH;
USE DATABASE DROPSHIPPING_DB;

-- 1. Count records in raw vs prod
SELECT 
    'Raw Events' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record
FROM raw.orders_events
UNION ALL
SELECT 
    'Production Orders' as table_name,
    COUNT(*) as record_count,
    MIN(ingested_at) as earliest_record,
    MAX(ingested_at) as latest_record
FROM prod.orders;

-- 2. Check for duplicates in raw events
SELECT 
    'Raw Events Duplicates' as check_name,
    COUNT(*) as duplicate_count
FROM (
    SELECT event_id, COUNT(*) as cnt
    FROM raw.orders_events
    GROUP BY event_id
    HAVING COUNT(*) > 1
);

-- 3. Check for duplicates in prod orders
SELECT 
    'Production Orders Duplicates' as check_name,
    COUNT(*) as duplicate_count
FROM (
    SELECT order_id, COUNT(*) as cnt
    FROM prod.orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
);

-- 4. Data quality checks
SELECT 
    'Data Quality Issues' as check_name,
    COUNT(*) as issue_count,
    'NULL order_id' as issue_type
FROM raw.orders_events
WHERE payload:order:id IS NULL
UNION ALL
SELECT 
    'Data Quality Issues' as check_name,
    COUNT(*) as issue_count,
    'NULL product_id' as issue_type
FROM raw.orders_events
WHERE payload:order:product_id IS NULL
UNION ALL
SELECT 
    'Data Quality Issues' as check_name,
    COUNT(*) as issue_count,
    'Negative unit_price' as issue_type
FROM raw.orders_events
WHERE payload:order:unit_price::DECIMAL(10,2) < 0;

-- 5. Recent ingestion activity
SELECT 
    'Recent Activity' as metric_name,
    COUNT(*) as events_last_hour
FROM raw.orders_events
WHERE created_at >= DATEADD(hour, -1, CURRENT_TIMESTAMP());

-- 6. Task execution status
SELECT 
    'Task Status' as metric_name,
    STATE as task_state,
    SCHEDULED_TIME as last_scheduled,
    COMPLETED_TIME as last_completed
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE TASK_NAME = 'INGEST_ORDERS_TASK'
ORDER BY SCHEDULED_TIME DESC
LIMIT 1;

-- 7. Summary statistics
SELECT 
    'Summary' as metric_name,
    (SELECT COUNT(*) FROM raw.orders_events) as raw_events,
    (SELECT COUNT(*) FROM prod.orders) as prod_orders,
    (SELECT COUNT(DISTINCT customer_id) FROM prod.orders) as unique_customers,
    (SELECT COUNT(DISTINCT product_id) FROM prod.orders) as unique_products,
    (SELECT SUM(quantity * unit_price) FROM prod.orders) as total_revenue;
