#!/usr/bin/env python3
"""
Export seed data script for dropshipping pipeline.
Generates customers, inventory, and orders data and exports to CSV files.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path to import data generator
sys.path.append(str(Path(__file__).parent.parent))

from data_generator import generate_customers, generate_inventory_data, generate_orders


def export_to_csv(df, filepath, description):
    """Export DataFrame to CSV with proper formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Format datetime columns to ISO 8601 UTC
    if 'sold_at' in df.columns:
        df['sold_at'] = df['sold_at'].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Ensure numeric columns have proper decimal formatting
    if 'unit_price' in df.columns:
        df['unit_price'] = df['unit_price'].round(2)
    
    df.to_csv(filepath, index=False)
    print(f"✅ Exported {len(df)} {description} to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Generate and export seed data for dropshipping pipeline")
    parser.add_argument("--customers", type=int, default=1000, help="Number of customers to generate")
    parser.add_argument("--products", type=int, default=200, help="Number of products to generate")
    parser.add_argument("--orders", type=int, default=5000, help="Number of orders to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data/seed", help="Output directory for CSV files")
    
    args = parser.parse_args()
    
    print(f"🚀 Generating seed data with parameters:")
    print(f"   - Customers: {args.customers}")
    print(f"   - Products: {args.products}")
    print(f"   - Orders: {args.orders}")
    print(f"   - Seed: {args.seed}")
    print(f"   - Output: {args.output_dir}")
    
    # Generate customers
    print("\n📊 Generating customers...")
    customers_df = generate_customers(customers=args.customers, seed=args.seed)
    export_to_csv(customers_df, f"{args.output_dir}/customers.csv", "customers")
    
    # Generate inventory
    print("\n📦 Generating inventory...")
    inventory_df = generate_inventory_data(products=args.products, seed=args.seed)
    export_to_csv(inventory_df, f"{args.output_dir}/inventory.csv", "products")
    
    # Generate orders
    print("\n🛒 Generating orders...")
    orders_df = generate_orders(
        orders=args.orders, 
        seed=args.seed,
        inventory=inventory_df,
        customers=customers_df
    )
    export_to_csv(orders_df, f"{args.output_dir}/orders.csv", "orders")
    
    print(f"\n✅ All seed data exported successfully to {args.output_dir}/")
    print(f"   - customers.csv: {len(customers_df)} records")
    print(f"   - inventory.csv: {len(inventory_df)} records")
    print(f"   - orders.csv: {len(orders_df)} records")


if __name__ == "__main__":
    main()
