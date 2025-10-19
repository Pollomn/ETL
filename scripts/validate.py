#!/usr/bin/env python3
"""
Validation script for dropshipping pipeline.
Checks data quality and generates validation report.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv


class PipelineValidator:
    def __init__(self, snowflake_config):
        self.snowflake_config = snowflake_config
        self.conn = None
        self.cursor = None
        self.results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {},
            'summary': {},
            'status': 'PASS'
        }
    
    def connect(self):
        """Connect to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.snowflake_config['account'],
                user=self.snowflake_config['user'],
                password=self.snowflake_config['password'],
                role=self.snowflake_config['role'],
                warehouse=self.snowflake_config['warehouse'],
                database=self.snowflake_config['database'],
                schema=self.snowflake_config['schema']
            )
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to Snowflake: {self.snowflake_config['account']}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Snowflake: {e}")
            return False
    
    def execute_query(self, query, description):
        """Execute a query and return results."""
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            # Convert to list of dicts
            data = []
            for row in results:
                data.append(dict(zip(columns, row)))
            
            print(f"✅ {description}: {len(data)} results")
            return data
        except Exception as e:
            print(f"❌ Query failed ({description}): {e}")
            return []
    
    def check_raw_vs_prod_counts(self):
        """Check record counts between raw and production tables."""
        print("\n📊 Checking raw vs production counts...")
        
        query = """
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
            FROM prod.orders
        """
        
        results = self.execute_query(query, "Raw vs Production counts")
        
        if len(results) >= 2:
            raw_count = results[0]['record_count']
            prod_count = results[1]['record_count']
            
            self.results['checks']['raw_vs_prod_counts'] = {
                'raw_count': raw_count,
                'prod_count': prod_count,
                'difference': raw_count - prod_count,
                'status': 'PASS' if raw_count >= prod_count else 'FAIL'
            }
            
            if raw_count < prod_count:
                self.results['status'] = 'FAIL'
                print(f"⚠️  Warning: Production has more records than raw ({prod_count} > {raw_count})")
        else:
            self.results['checks']['raw_vs_prod_counts'] = {
                'status': 'ERROR',
                'message': 'Could not retrieve counts'
            }
            self.results['status'] = 'FAIL'
    
    def check_duplicates(self):
        """Check for duplicate records."""
        print("\n🔍 Checking for duplicates...")
        
        # Check raw events duplicates
        query = """
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT event_id, COUNT(*) as cnt
                FROM raw.orders_events
                GROUP BY event_id
                HAVING COUNT(*) > 1
            )
        """
        
        results = self.execute_query(query, "Raw events duplicates")
        raw_duplicates = results[0]['duplicate_count'] if results else 0
        
        # Check prod orders duplicates
        query = """
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT order_id, COUNT(*) as cnt
                FROM prod.orders
                GROUP BY order_id
                HAVING COUNT(*) > 1
            )
        """
        
        results = self.execute_query(query, "Production orders duplicates")
        prod_duplicates = results[0]['duplicate_count'] if results else 0
        
        self.results['checks']['duplicates'] = {
            'raw_duplicates': raw_duplicates,
            'prod_duplicates': prod_duplicates,
            'status': 'PASS' if raw_duplicates == 0 and prod_duplicates == 0 else 'FAIL'
        }
        
        if raw_duplicates > 0 or prod_duplicates > 0:
            self.results['status'] = 'FAIL'
            print(f"⚠️  Found duplicates: {raw_duplicates} in raw, {prod_duplicates} in prod")
    
    def check_data_quality(self):
        """Check data quality issues."""
        print("\n🔍 Checking data quality...")
        
        query = """
            SELECT 
                'NULL order_id' as issue_type,
                COUNT(*) as issue_count
            FROM raw.orders_events
            WHERE payload:order:id IS NULL
            UNION ALL
            SELECT 
                'NULL product_id' as issue_type,
                COUNT(*) as issue_count
            FROM raw.orders_events
            WHERE payload:order:product_id IS NULL
            UNION ALL
            SELECT 
                'Negative unit_price' as issue_type,
                COUNT(*) as issue_count
            FROM raw.orders_events
            WHERE payload:order:unit_price::DECIMAL(10,2) < 0
        """
        
        results = self.execute_query(query, "Data quality issues")
        
        total_issues = sum(row['issue_count'] for row in results)
        
        self.results['checks']['data_quality'] = {
            'issues': results,
            'total_issues': total_issues,
            'status': 'PASS' if total_issues == 0 else 'FAIL'
        }
        
        if total_issues > 0:
            self.results['status'] = 'FAIL'
            print(f"⚠️  Found {total_issues} data quality issues")
    
    def check_recent_activity(self):
        """Check recent ingestion activity."""
        print("\n⏰ Checking recent activity...")
        
        query = """
            SELECT COUNT(*) as events_last_hour
            FROM raw.orders_events
            WHERE created_at >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
        """
        
        results = self.execute_query(query, "Recent activity")
        recent_events = results[0]['events_last_hour'] if results else 0
        
        self.results['checks']['recent_activity'] = {
            'events_last_hour': recent_events,
            'status': 'PASS' if recent_events > 0 else 'WARN'
        }
        
        if recent_events == 0:
            print("⚠️  No events in the last hour")
    
    def check_task_status(self):
        """Check task execution status."""
        print("\n⚙️  Checking task status...")
        
        query = """
            SELECT 
                STATE as task_state,
                SCHEDULED_TIME as last_scheduled,
                COMPLETED_TIME as last_completed,
                ERROR_MESSAGE as error_message
            FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
            WHERE TASK_NAME = 'INGEST_ORDERS_TASK'
            ORDER BY SCHEDULED_TIME DESC
            LIMIT 1
        """
        
        results = self.execute_query(query, "Task status")
        
        if results:
            task_info = results[0]
            self.results['checks']['task_status'] = {
                'state': task_info['task_state'],
                'last_scheduled': str(task_info['last_scheduled']) if task_info['last_scheduled'] else None,
                'last_completed': str(task_info['last_completed']) if task_info['last_completed'] else None,
                'error_message': task_info['error_message'],
                'status': 'PASS' if task_info['task_state'] == 'SUCCEEDED' else 'FAIL'
            }
            
            if task_info['task_state'] != 'SUCCEEDED':
                self.results['status'] = 'FAIL'
                print(f"⚠️  Task status: {task_info['task_state']}")
                if task_info['error_message']:
                    print(f"   Error: {task_info['error_message']}")
        else:
            self.results['checks']['task_status'] = {
                'status': 'ERROR',
                'message': 'Could not retrieve task status'
            }
            self.results['status'] = 'FAIL'
    
    def generate_summary(self):
        """Generate summary statistics."""
        print("\n📈 Generating summary...")
        
        query = """
            SELECT 
                (SELECT COUNT(*) FROM raw.orders_events) as raw_events,
                (SELECT COUNT(*) FROM prod.orders) as prod_orders,
                (SELECT COUNT(DISTINCT customer_id) FROM prod.orders) as unique_customers,
                (SELECT COUNT(DISTINCT product_id) FROM prod.orders) as unique_products,
                (SELECT SUM(quantity * unit_price) FROM prod.orders) as total_revenue
        """
        
        results = self.execute_query(query, "Summary statistics")
        
        if results:
            summary = results[0]
            self.results['summary'] = {
                'raw_events': summary['raw_events'],
                'prod_orders': summary['prod_orders'],
                'unique_customers': summary['unique_customers'],
                'unique_products': summary['unique_products'],
                'total_revenue': float(summary['total_revenue']) if summary['total_revenue'] else 0
            }
            
            print(f"📊 Summary:")
            print(f"   Raw events: {summary['raw_events']}")
            print(f"   Production orders: {summary['prod_orders']}")
            print(f"   Unique customers: {summary['unique_customers']}")
            print(f"   Unique products: {summary['unique_products']}")
            print(f"   Total revenue: ${summary['total_revenue']:,.2f}")
    
    def save_report(self):
        """Save validation report to JSON file."""
        os.makedirs('reports', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reports/validate_report_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Validation report saved to: {filename}")
        return filename
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    # Load environment variables
    load_dotenv()
    
    # Snowflake configuration
    snowflake_config = {
        'account': os.getenv('SNOW_ACCOUNT'),
        'user': os.getenv('SNOW_USER'),
        'password': os.getenv('SNOW_PASSWORD'),
        'role': os.getenv('SNOW_ROLE', 'ACCOUNTADMIN'),
        'warehouse': os.getenv('SNOW_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOW_DATABASE', 'DROPSHIPPING_DB'),
        'schema': os.getenv('SNOW_SCHEMA', 'RAW')
    }
    
    # Validate required environment variables
    required_vars = ['SNOW_ACCOUNT', 'SNOW_USER', 'SNOW_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Create a .env file with your Snowflake credentials")
        sys.exit(1)
    
    print("🔍 Starting pipeline validation...")
    
    validator = PipelineValidator(snowflake_config)
    
    if not validator.connect():
        sys.exit(1)
    
    try:
        # Run all validation checks
        validator.check_raw_vs_prod_counts()
        validator.check_duplicates()
        validator.check_data_quality()
        validator.check_recent_activity()
        validator.check_task_status()
        validator.generate_summary()
        
        # Save report
        report_file = validator.save_report()
        
        # Print final status
        print(f"\n🎯 Validation Status: {validator.results['status']}")
        
        if validator.results['status'] == 'PASS':
            print("✅ All checks passed!")
            sys.exit(0)
        else:
            print("❌ Some checks failed. See report for details.")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)
    finally:
        validator.close()


if __name__ == "__main__":
    main()
