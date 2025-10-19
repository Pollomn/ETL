#!/bin/bash
# Script to run all Snowflake SQL files in sequence
# Usage: ./run_all.sh

set -e  # Exit on any error

echo "🚀 Starting Snowflake setup..."

# Check if snowsql is available
if ! command -v snowsql &> /dev/null; then
    echo "❌ snowsql command not found. Please install SnowSQL first."
    echo "💡 Download from: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one from .env.example"
    echo "💡 Copy .env.example to .env and fill in your Snowflake credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Validate required environment variables
required_vars=("SNOW_ACCOUNT" "SNOW_USER" "SNOW_PASSWORD" "SNOW_ROLE" "SNOW_WAREHOUSE" "SNOW_DATABASE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done

echo "✅ Environment variables loaded"
echo "   Account: $SNOW_ACCOUNT"
echo "   User: $SNOW_USER"
echo "   Warehouse: $SNOW_WAREHOUSE"
echo "   Database: $SNOW_DATABASE"

# Function to run SQL file
run_sql_file() {
    local file=$1
    local description=$2
    
    echo ""
    echo "📄 Running $description..."
    echo "   File: $file"
    
    if snowsql -a "$SNOW_ACCOUNT" -u "$SNOW_USER" -p "$SNOW_PASSWORD" -r "$SNOW_ROLE" -w "$SNOW_WAREHOUSE" -d "$SNOW_DATABASE" -f "$file" -o exit_on_error=true; then
        echo "✅ $description completed successfully"
    else
        echo "❌ $description failed"
        exit 1
    fi
}

# Run SQL files in sequence
run_sql_file "01_create_warehouse_db_schemas.sql" "Warehouse and Database Setup"
run_sql_file "02_create_tables.sql" "Table Creation"
run_sql_file "03_create_stream_and_task.sql" "Stream and Task Setup"
run_sql_file "04_validate_ingestion.sql" "Validation Queries"

echo ""
echo "🎉 All Snowflake setup completed successfully!"
echo ""
echo "📊 Next steps:"
echo "   1. Start Kafka producer: python scripts/producer.py --mode replay --rate 10"
echo "   2. Start Kafka consumer: python scripts/consumer_snowflake.py"
echo "   3. Run validation: python scripts/validate.py"
echo "   4. Start monitoring: streamlit run streamlit_monitor/app.py"
