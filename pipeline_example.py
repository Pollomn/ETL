"""
🎓 ETL PIPELINE EXAMPLE - STUDENT TEMPLATE
=========================================

This is a LEARNING TEMPLATE for students to understand ETL pipeline concepts.

PURPOSE:
- Learn how to extract data from various sources
- Understand data transformation processes
- Practice loading data into a data warehouse (Snowflake)
- Implement the ELT (Extract, Load, Transform) pattern

INSTRUCTIONS FOR STUDENTS:
1. Read through all comments carefully
2. Replace placeholder values with your actual database credentials
3. Modify the data transformation logic as needed
4. Test each step incrementally
5. Add error handling and logging as you learn

AUTHOR: Lore Pascale Alechou-Tacite
COURSE: Data Warehousing & ETL
DATE: September 2025
"""

import os

import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

from utils.data_generator import (
    generate_customers,
    generate_inventory_data,
    generate_orders,
)


# --- 1. SETUP AND CONFIGURATION ---
# 📚 STUDENT NOTE: This section shows how to securely manage database credentials
# 📚 STUDENT TASK: Create a .env file with your actual credentials
# 🔐 SECURITY NOTE: Never commit credentials to version control!

"""
🎯 STUDENT ASSIGNMENT: Create your .env file
==========================================

Copy the template below and replace with YOUR actual credentials:

# Source database credentials (if using a source DB)
SOURCE_DB_USER="your_db_username_here"
SOURCE_DB_PASSWORD="your_db_password_here"
SOURCE_DB_HOST="localhost_or_remote_host"
SOURCE_DB_PORT="5432"
SOURCE_DB_NAME="your_database_name"

# Snowflake credentials (REQUIRED - get these from your Snowflake account)
SNOWFLAKE_ACCOUNT="your_account_identifier"  # TODO: Replace with your Snowflake account
SNOWFLAKE_USER="YOUR_USERNAME"              # TODO: Replace with your Snowflake username
SNOWFLAKE_PASSWORD="your_password"          # TODO: Replace with your Snowflake password
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"            # Default warehouse name
SNOWFLAKE_DATABASE="YOUR_DATABASE"          # TODO: Replace with your database name
SNOWFLAKE_SCHEMA="PUBLIC"                   # Default schema
SNOWFLAKE_ROLE=""                           # Optional: specify role if needed

"""
load_dotenv()


# Get database credentials from environment variables
# Source DB
source_user = os.getenv("SOURCE_DB_USER")
source_password = os.getenv("SOURCE_DB_PASSWORD")
source_host = os.getenv("SOURCE_DB_HOST")
source_port = os.getenv("SOURCE_DB_PORT")
source_db = os.getenv("SOURCE_DB_NAME")

# Snowflake
sf_user = os.getenv("SNOWFLAKE_USER")
sf_password = os.getenv("SNOWFLAKE_PASSWORD")
sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
sf_database = os.getenv("SNOWFLAKE_DATABASE")
sf_schema = os.getenv("SNOWFLAKE_SCHEMA")

# --- MAIN PIPELINE EXECUTION ---


def main():
    """Run the educational ELT pipeline example.

    This function illustrates (for teaching purposes) the typical sequence of an
    ELT pipeline that lands data in Snowflake:

    1. CONNECT  - Open a connection to the destination warehouse (Snowflake).
    2. STAGE    - Create (or reuse) a staging table for raw / incoming data.
    3. EXTRACT  - (Here simulated) Obtain source data (could be DB/API/files in real life).
    4. TRANSFORM - (Minimal here) Prepare / clean / conform the data to your target schema.
    5. LOAD     - Bulk load into the staging area.
    6. MERGE    - Upsert from staging into the final analytical table.

    Student Objectives:
    - Trace the flow of data end-to-end.
    - Identify where to add validations, profiling, logging.
    - Practice modifying SQL to fit a real business schema.
    - Understand why staging decouples raw ingestion from curated tables.

    Suggested Exercises:
    - Add a data quality check (e.g., ensure QUANTITY > 0).
    - Parameterize number of generated orders via CLI arguments.
    - Add a "load timestamp" column populated with current time.
    - Replace the simulated extract with a real source (CSV / API / Postgres).
    """

    print("🚀 Starting ETL Pipeline (Educational Mode)")
    # Track connection so we can always close it in finally
    sf_connection = None

    # TABLE NAMING GUIDANCE:
    # - Use uppercase (Snowflake convention) for physical table names
    # - Prefix staging tables with STG_ or end with _STG for clarity
    staging_table = "ORDERS_STG"  # TODO: Rename to match your naming standards
    target_table = "ORDERS_ANALYTICS"  # TODO: Create or point to your final table

    try:
        # --- STEP 1: CONNECT -------------------------------------------------
        print("🔌 Connecting to Snowflake ...")
        sf_connection = snowflake.connector.connect(
            user=sf_user,
            password=sf_password,
            account=sf_account,
            warehouse=sf_warehouse,
            database=sf_database,
            schema=sf_schema,
        )
        print("✅ Connected to Snowflake")
        print(f"   → Database: {sf_database} | Schema: {sf_schema} | Warehouse: {sf_warehouse}")

        # --- STEP 2: PREP STAGING TABLE -------------------------------------
        # Use a TEMP table for classroom safety (it vanishes when session ends).
        # Swap TEMP with a permanent table if you need persistence across sessions.
        sf_cursor = sf_connection.cursor()
        print(f"🧱 Ensuring staging table {staging_table} exists (TEMP)...")
        sf_cursor.execute(f"""
            CREATE OR REPLACE TEMP TABLE {staging_table} (
                ORDER_ID INTEGER,
                CUSTOMER_ID INTEGER,
                PRODUCT_ID INTEGER,
                QUANTITY INTEGER,
                UNIT_PRICE DECIMAL(10,2),
                ORDER_TOTAL DECIMAL(10,2),
                SOLD_AT TIMESTAMP
            )
        """)
        print("✅ Staging table ready")

        # --- STEP 3: EXTRACT (SIMULATED) ------------------------------------
        # In real projects this might query a source DB or call an API.
        print("📥 Generating sample source data (simulated extract)...")
        customers_df = generate_customers(customers=100, seed=21)
        inventory_df = generate_inventory_data(products=19, seed=23)
        orders_df = generate_orders(
            customers=customers_df,
            inventory=inventory_df,
            orders=1000,
            seed=32,
        )
        print(f"   → Generated {len(orders_df)} order rows")

        # --- STEP 4: TRANSFORM (LIGHT TOUCH HERE) ---------------------------
        # PLACEHOLDER: Insert your data quality & transformation logic.
        # Examples to try:
        #   - Drop duplicates on ORDER_ID
        #   - Enforce data types (e.g., QUANTITY as int)
        #   - Compute ORDER_TOTAL if missing: QUANTITY * UNIT_PRICE
        #   - Filter out invalid rows (negative quantities)
        print("🧪 Preparing data for load (copying DataFrame)...")
        orders_to_load = orders_df.copy()
        # Example (uncomment to enforce positivity):
        # orders_to_load = orders_to_load[orders_to_load["QUANTITY"] > 0]

        # --- STEP 5: LOAD TO STAGING ----------------------------------------
        print(f"📤 Loading {len(orders_to_load)} rows into staging table {staging_table} ...")
        write_pandas(
            sf_connection,
            orders_to_load,
            staging_table,
            auto_create_table=False,  # We already created schema explicitly
            overwrite=True,  # For classroom simplicity; replace each run
        )
        print("✅ Data loaded into staging")

        # --- STEP 6: MERGE INTO TARGET --------------------------------------
        # UPSERT pattern: update matching rows, insert new ones.
        merge_sql = f"""
        MERGE INTO {target_table} AS T
        USING {staging_table} AS S
            ON T.ORDER_ID = S.ORDER_ID
        WHEN MATCHED THEN UPDATE SET
            T.CUSTOMER_ID = S.CUSTOMER_ID,
            T.PRODUCT_ID  = S.PRODUCT_ID,
            T.QUANTITY    = S.QUANTITY,
            T.UNIT_PRICE  = S.UNIT_PRICE,
            T.ORDER_TOTAL = S.ORDER_TOTAL,
            T.SOLD_AT     = S.SOLD_AT
        WHEN NOT MATCHED THEN INSERT (
            ORDER_ID, CUSTOMER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, ORDER_TOTAL, SOLD_AT
        ) VALUES (
            S.ORDER_ID, S.CUSTOMER_ID, S.PRODUCT_ID, S.QUANTITY, S.UNIT_PRICE, S.ORDER_TOTAL, S.SOLD_AT
        );
        """

        print(f"🔀 Executing MERGE into target table {target_table} ...")
        # Print or log SQL for transparency (good for debugging / demos)
        print("--- MERGE STATEMENT START ---")
        print(merge_sql.strip())
        print("--- MERGE STATEMENT END ---")
        sf_cursor.execute(merge_sql)
        print("✅ Merge completed")

        print("🎉 Pipeline run completed successfully")

    except Exception as e:
        print("❌ PIPELINE FAILED")
        print(f"   → Error Type: {type(e).__name__}")
        print(f"   → Message   : {e}")
        print("🛠️  Debug Checklist:")
        print("  1. Did you create & populate your .env file?")
        print("  2. Are Snowflake credentials correct (account / user / warehouse / db / schema)?")
        print("  3. Does the target table exist (if not, create it first)?")
        print("  4. Do the column names in staging & target match exactly?")
        print("  5. Are data types compatible (e.g., DECIMAL vs INTEGER)?")
        print("  6. If still stuck, copy the stack trace & ask your instructor.")
        raise
    finally:
        # Always clean up connections; TEMP tables vanish automatically.
        if sf_connection is not None:
            try:
                sf_connection.close()
                print("🔌 Closed Snowflake connection")
            except Exception:
                pass


if __name__ == "__main__":
    # Optional: Add CLI parsing here (argparse / click) to parameterize run.
    # For now we just execute main().
    main()
