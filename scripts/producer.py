#!/usr/bin/env python3
"""
Kafka producer for dropshipping pipeline.
Supports two modes: replay (from CSV) and stream (continuous generation).
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer
from dotenv import load_dotenv

# Add parent directory to path to import data generator
sys.path.append(str(Path(__file__).parent.parent))
from data_generator import generate_orders


class OrderProducer:
    def __init__(self, bootstrap_servers, topic):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.running = True
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def connect(self):
        """Connect to Kafka broker."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                acks='all',
                compression_type='gzip',
                request_timeout_ms=30000,
                metadata_max_age_ms=30000,
                connections_max_idle_ms=30000
            )
            print(f"✅ Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def send_order_event(self, order_data):
        """Send a single order event to Kafka."""
        try:
            event = {
                "event_type": "order_created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "order": order_data
            }
            
            # Use order_id as key for partitioning
            key = str(order_data.get('id', ''))
            
            future = self.producer.send(self.topic, value=event, key=key)
            future.get(timeout=30)  # Wait for confirmation with longer timeout
            
            return True
        except Exception as e:
            print(f"❌ Failed to send order event: {e}")
            return False
    
    def replay_mode(self, csv_file, rate):
        """Replay orders from CSV file at specified rate."""
        print(f"📂 Loading orders from {csv_file}")
        
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 Loaded {len(df)} orders from CSV")
        except Exception as e:
            print(f"❌ Failed to load CSV file: {e}")
            return False
        
        print(f"🚀 Starting replay at {rate} events/second...")
        print("Press Ctrl+C to stop")
        
        sent_count = 0
        start_time = time.time()
        
        for _, row in df.iterrows():
            if not self.running:
                break
                
            # Convert row to dict and handle datetime
            order_data = row.to_dict()
            if 'sold_at' in order_data and pd.notna(order_data['sold_at']):
                # Ensure sold_at is properly formatted
                if isinstance(order_data['sold_at'], str):
                    order_data['sold_at'] = order_data['sold_at']
                else:
                    order_data['sold_at'] = pd.to_datetime(order_data['sold_at']).isoformat()
            
            if self.send_order_event(order_data):
                sent_count += 1
                if sent_count % 100 == 0:
                    print(f"📤 Sent {sent_count} events...")
            
            # Rate limiting
            if rate > 0:
                time.sleep(1.0 / rate)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Replay completed: {sent_count} events sent in {elapsed:.2f}s")
        return True
    
    def stream_mode(self, customers_df, inventory_df, rate):
        """Generate and send orders continuously."""
        print(f"🌊 Starting continuous stream at {rate} events/second...")
        print("Press Ctrl+C to stop")
        
        sent_count = 0
        start_time = time.time()
        
        while self.running:
            # Generate a single order
            orders_df = generate_orders(
                orders=1,
                seed=int(time.time() * 1000) % 1000000,  # Use timestamp as seed
                inventory=inventory_df,
                customers=customers_df
            )
            
            order_data = orders_df.iloc[0].to_dict()
            if 'sold_at' in order_data:
                order_data['sold_at'] = pd.to_datetime(order_data['sold_at']).isoformat()
            
            if self.send_order_event(order_data):
                sent_count += 1
                if sent_count % 50 == 0:
                    elapsed = time.time() - start_time
                    print(f"📤 Sent {sent_count} events in {elapsed:.2f}s (avg: {sent_count/elapsed:.2f}/s)")
            
            # Rate limiting
            if rate > 0:
                time.sleep(1.0 / rate)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Stream completed: {sent_count} events sent in {elapsed:.2f}s")
        return True
    
    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            print("🔌 Producer connection closed")


def main():
    parser = argparse.ArgumentParser(description="Kafka producer for dropshipping orders")
    parser.add_argument("--mode", choices=["replay", "stream"], required=True,
                       help="Producer mode: replay (from CSV) or stream (continuous)")
    parser.add_argument("--file", type=str, default="data/seed/orders.csv",
                       help="CSV file for replay mode")
    parser.add_argument("--rate", type=float, default=10.0,
                       help="Events per second (0 = no rate limiting)")
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9092",
                       help="Kafka bootstrap servers")
    parser.add_argument("--topic", type=str, default="orders_topic",
                       help="Kafka topic name")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Override with environment variables if available
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', args.bootstrap_servers)
    topic = os.getenv('KAFKA_TOPIC', args.topic)
    
    print(f"🚀 Starting Kafka producer")
    print(f"   Mode: {args.mode}")
    print(f"   Bootstrap servers: {bootstrap_servers}")
    print(f"   Topic: {topic}")
    print(f"   Rate: {args.rate} events/sec")
    
    producer = OrderProducer(bootstrap_servers, topic)
    
    if not producer.connect():
        sys.exit(1)
    
    try:
        if args.mode == "replay":
            if not os.path.exists(args.file):
                print(f"❌ CSV file not found: {args.file}")
                print("💡 Run 'python scripts/export_seed.py' first to generate data")
                sys.exit(1)
            producer.replay_mode(args.file, args.rate)
        
        elif args.mode == "stream":
            # Load reference data for stream mode
            try:
                customers_df = pd.read_csv("data/seed/customers.csv")
                inventory_df = pd.read_csv("data/seed/inventory.csv")
                print(f"📊 Loaded reference data: {len(customers_df)} customers, {len(inventory_df)} products")
            except Exception as e:
                print(f"❌ Failed to load reference data: {e}")
                print("💡 Run 'python scripts/export_seed.py' first to generate data")
                sys.exit(1)
            
            producer.stream_mode(customers_df, inventory_df, args.rate)
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Producer error: {e}")
        sys.exit(1)
    finally:
        producer.close()


if __name__ == "__main__":
    main()
