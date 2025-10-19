-- Create stream and task for automated data processing
-- This script is idempotent and can be run multiple times safely

-- Set context
USE WAREHOUSE mon_entrepot;
USE DATABASE ma_base;
USE SCHEMA mon_schema;

-- Create stream on orders_events table
CREATE STREAM IF NOT EXISTS mon_schema.orders_stream 
ON TABLE mon_schema.orders_events
COMMENT = 'Stream for new order events';

-- Create task to process new events
CREATE TASK IF NOT EXISTS mon_schema.ingest_orders_task
    WAREHOUSE = mon_entrepot
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('mon_schema.orders_stream')
AS
    -- Merge new orders into mon_schema.orders
    MERGE INTO mon_schema.orders t 
    USING (
        SELECT 
            payload:order:id::INTEGER AS order_id,
            payload:order:product_id::INTEGER AS product_id,
            payload:order:customer_id::INTEGER AS customer_id,
            payload:order:quantity::INTEGER AS quantity,
            payload:order:unit_price::DECIMAL(10,2) AS unit_price,
            payload:order:sold_at::TIMESTAMP_NTZ AS sold_at,
            CURRENT_TIMESTAMP() AS ingested_at
        FROM mon_schema.orders_stream 
        WHERE METADATA$ACTION = 'INSERT'
    ) s ON t.order_id = s.order_id
    WHEN NOT MATCHED THEN 
        INSERT (order_id, product_id, customer_id, quantity, unit_price, sold_at, ingested_at)
        VALUES (s.order_id, s.product_id, s.customer_id, s.quantity, s.unit_price, s.sold_at, s.ingested_at);

-- Resume the task (it starts suspended by default)
ALTER TASK mon_schema.ingest_orders_task RESUME;

-- Show task status
SHOW TASKS IN SCHEMA mon_schema;
SHOW STREAMS IN SCHEMA mon_schema;
