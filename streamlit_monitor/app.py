#!/usr/bin/env python3
"""
Streamlit dashboard for dropshipping pipeline monitoring.
Displays KPIs, top products, and recent orders.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class DropshippingDashboard:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.snowflake_config = self._load_config()
    
    def _load_config(self):
        """Load Snowflake configuration from environment."""
        load_dotenv()
        
        return {
            'account': os.getenv('SNOW_ACCOUNT'),
            'user': os.getenv('SNOW_USER'),
            'password': os.getenv('SNOW_PASSWORD'),
            'role': os.getenv('SNOW_ROLE', 'ACCOUNTADMIN'),
            'warehouse': os.getenv('SNOW_WAREHOUSE', 'COMPUTE_WH'),
            'database': os.getenv('SNOW_DATABASE', 'DROPSHIPPING_DB'),
            'schema': os.getenv('SNOW_SCHEMA', 'RAW')
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
            return True
        except Exception as e:
            st.error(f"Failed to connect to Snowflake: {e}")
            return False
    
    def execute_query(self, query):
        """Execute a query and return DataFrame."""
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return pd.DataFrame(results, columns=columns)
        except Exception as e:
            st.error(f"Query failed: {e}")
            return pd.DataFrame()
    
    def get_kpis(self):
        """Get key performance indicators."""
        query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(quantity * unit_price) as TOTAL_REVENUE,
                COUNT(DISTINCT customer_id) as unique_customers,
                COUNT(DISTINCT product_id) as unique_products
            FROM mon_schema.orders
        """
        
        df = self.execute_query(query)
        if not df.empty:
            return df.iloc[0].to_dict()
        return {}
    
    def get_recent_orders(self, hours=24):
        """Get recent orders."""
        query = f"""
            SELECT 
                o.id as order_id,
                o.customer_id,
                c.name as CUSTOMER_NAME,
                o.product_id,
                p.product_name as PRODUCT_NAME,
                o.quantity,
                o.unit_price,
                o.sold_at,
                (o.quantity * o.unit_price) as total_amount
            FROM mon_schema.orders o
            JOIN mon_schema.customers c ON o.customer_id = c.customer_id
            JOIN mon_schema.inventory p ON o.product_id = p.product_id
            WHERE o.sold_at >= DATEADD(hour, -{hours}, CURRENT_TIMESTAMP())
            ORDER BY o.sold_at DESC
            LIMIT 20
        """
        
        return self.execute_query(query)
    
    def get_top_products(self, limit=5):
        """Get top products by volume and revenue."""
        query = f"""
            SELECT 
                p.product_id,
                p.product_name as PRODUCT_NAME,
                p.category as CATEGORY,
                SUM(o.quantity) as TOTAL_QUANTITY,
                SUM(o.quantity * o.unit_price) as TOTAL_REVENUE,
                COUNT(*) as ORDER_COUNT
            FROM mon_schema.orders o
            JOIN mon_schema.inventory p ON o.product_id = p.product_id
            GROUP BY p.product_id, p.product_name, p.category
            ORDER BY TOTAL_REVENUE DESC
            LIMIT {limit}
        """
        
        return self.execute_query(query)
    
    def get_daily_orders(self, days=7):
        """Get daily order counts for the last N days."""
        query = f"""
            SELECT 
                DATE(sold_at) as order_date,
                COUNT(*) as ORDER_COUNT,
                SUM(quantity * unit_price) as daily_revenue
            FROM mon_schema.orders
            WHERE sold_at >= DATEADD(day, -{days}, CURRENT_DATE())
            GROUP BY DATE(sold_at)
            ORDER BY order_date
        """
        
        return self.execute_query(query)
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    st.set_page_config(
        page_title="Dropshipping Pipeline Monitor",
        page_icon="🛒",
        layout="wide"
    )
    
    st.title("🛒 Dropshipping Pipeline Monitor")
    st.markdown("Real-time monitoring of the dropshipping data pipeline")
    
    # Initialize dashboard
    dashboard = DropshippingDashboard()
    
    # Connect to database
    if not dashboard.connect():
        st.stop()
    
    try:
        # Sidebar controls
        st.sidebar.header("📊 Controls")
        
        # Time range selector
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last 24 hours", "Last 7 days", "Last 30 days"],
            index=0
        )
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
            time.sleep(30)
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("📈 Key Performance Indicators")
            
            # Get KPIs
            kpis = dashboard.get_kpis()
            
            if kpis:
                col1_1, col1_2, col1_3, col1_4 = st.columns(4)
                
                with col1_1:
                    st.metric(
                        label="Total Orders",
                        value=f"{kpis.get('total_orders', 0):,}",
                        delta=None
                    )
                
                with col1_2:
                    st.metric(
                        label="Total Revenue",
                        value=f"${kpis.get('TOTAL_REVENUE', 0):,.2f}",
                        delta=None
                    )
                
                with col1_3:
                    st.metric(
                        label="Unique Customers",
                        value=f"{kpis.get('unique_customers', 0):,}",
                        delta=None
                    )
                
                with col1_4:
                    st.metric(
                        label="Unique Products",
                        value=f"{kpis.get('unique_products', 0):,}",
                        delta=None
                    )
            
            # Top products chart
            st.header("🏆 Top Products")
            
            top_products = dashboard.get_top_products()
            
            if not top_products.empty:
                # Create bar chart
                fig = px.bar(
                    top_products,
                    x='TOTAL_REVENUE',
                    y='PRODUCT_NAME',
                    orientation='h',
                    title="Top Products by Revenue",
                    labels={'TOTAL_REVENUE': 'Revenue ($)', 'PRODUCT_NAME': 'Product'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top products table
                st.subheader("📊 Top Products Details")
                st.dataframe(
                    top_products[['PRODUCT_NAME', 'CATEGORY', 'TOTAL_QUANTITY', 'TOTAL_REVENUE', 'ORDER_COUNT']],
                    use_container_width=True
                )
            else:
                st.info("No product data available")
        
        with col2:
            st.header("📅 Recent Orders")
            
            # Get recent orders
            recent_orders = dashboard.get_recent_orders()
            
            if not recent_orders.empty:
                st.dataframe(
                    recent_orders[['CUSTOMER_NAME', 'PRODUCT_NAME', 'quantity', 'total_amount', 'sold_at']],
                    use_container_width=True
                )
            else:
                st.info("No recent orders found")
        
        # Daily trends
        st.header("📈 Daily Trends")
        
        daily_orders = dashboard.get_daily_orders()
        
        if not daily_orders.empty:
            col3_1, col3_2 = st.columns(2)
            
            with col3_1:
                # Orders chart
                fig_orders = px.line(
                    daily_orders,
                    x='order_date',
                    y='ORDER_COUNT',
                    title="Daily Order Count",
                    labels={'ORDER_COUNT': 'Orders', 'order_date': 'Date'}
                )
                st.plotly_chart(fig_orders, use_container_width=True)
            
            with col3_2:
                # Revenue chart
                fig_revenue = px.line(
                    daily_orders,
                    x='order_date',
                    y='daily_revenue',
                    title="Daily Revenue",
                    labels={'daily_revenue': 'Revenue ($)', 'order_date': 'Date'}
                )
                st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No daily trend data available")
        
        # Footer
        st.markdown("---")
        st.markdown(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Pipeline Status: {'🟢 Active' if kpis else '🔴 Inactive'}"
        )
    
    except Exception as e:
        st.error(f"Dashboard error: {e}")
    finally:
        dashboard.close()


if __name__ == "__main__":
    main()
