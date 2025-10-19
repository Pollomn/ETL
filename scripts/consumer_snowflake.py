#!/usr/bin/env python3
"""
Kafka consumer for dropshipping pipeline.
Consumes order events and inserts them into Snowflake raw.orders_events table.
"""

import json
import os
import signal
import sys
import time
import uuid
from datetime import datetime, timezone

import snowflake.connector
from kafka import KafkaConsumer
from dotenv import load_dotenv


class OrderConsumer:
    def __init__(self, kafka_config, snowflake_config):
        self.kafka_config = kafka_config
        self.snowflake_config = snowflake_config
        self.consumer = None
        self.conn = None
        self.cursor = None
        self.running = True
        self.processed_count = 0
        self.error_count = 0
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def connect_kafka(self):
        """Connect to Kafka broker."""
        try:
            self.consumer = KafkaConsumer(
                self.kafka_config['topic'],
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                group_id='snowflake-consumer-group-debug',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=5000  # 5 secondes timeout
            )
            print(f"✅ Connected to Kafka: {self.kafka_config['bootstrap_servers']}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def connect_snowflake(self):
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
    
    def insert_event(self, event_data):
        """Insert a single event into Snowflake."""
        try:
            event_id = str(uuid.uuid4())
            event_type = event_data.get('event_type', 'unknown')
            payload = json.dumps(event_data.get('order', {}))
            created_at = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO MON_SCHEMA.orders_events (event_id, event_type, payload, created_at)
                VALUES (%s, %s, PARSE_JSON(%s), %s)
            """
            
            self.cursor.execute(query, (event_id, event_type, payload, created_at))
            self.conn.commit()
            
            return True
        except Exception as e:
            print(f"❌ Failed to insert event: {e}")
            self.error_count += 1
            return False
    
    def process_batch(self, messages):
        """Process a batch of messages."""
        batch_size = len(messages)
        print(f"📦 Processing batch of {batch_size} messages...")
        
        success_count = 0
        for message in messages:
            if not self.running:
                break
                
            try:
                event_data = message.value
                if self.insert_event(event_data):
                    success_count += 1
                    self.processed_count += 1
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                self.error_count += 1
        
        print(f"✅ Batch processed: {success_count}/{batch_size} successful")
        return success_count
    
    def run(self):
        """Main consumer loop."""
        print(f"🚀 Starting consumer for topic: {self.kafka_config['topic']}")
        print("Press Ctrl+C to stop")
        print("🔍 Debug: Waiting for messages...")
        
        batch = []
        batch_size = 10
        last_commit = time.time()
        commit_interval = 5  # seconds
        
        try:
            for message in self.consumer:
                print(f"🔍 Debug: Received message: {message}")
                if not self.running:
                    break
                
                batch.append(message)
                
                # Process batch when full or timeout
                current_time = time.time()
                if len(batch) >= batch_size or (last_commit is not None and (current_time - last_commit) >= commit_interval):
                    if batch:
                        self.process_batch(batch)
                        batch = []
                        last_commit = current_time
                
                # Periodic status update
                if self.processed_count is not None and self.processed_count > 0 and self.processed_count % 100 == 0:
                    print(f"📊 Status: {self.processed_count} processed, {self.error_count} errors")
        
        except Exception as e:
            import traceback
            print(f"❌ Consumer error: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return False
        
        # Process remaining messages
        if batch:
            self.process_batch(batch)
        
        print(f"\n✅ Consumer completed: {self.processed_count} events processed, {self.error_count} errors")
        return True
    
    def close(self):
        """Close connections."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        if self.consumer:
            self.consumer.close()
        print("🔌 Connections closed")


def main():
    # Load environment variables
    load_dotenv()
    
    # Kafka configuration
    kafka_config = {
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'topic': os.getenv('KAFKA_TOPIC', 'orders_topic')
    }
    
    # Snowflake configuration
    snowflake_config = {
        'account': os.getenv('SNOW_ACCOUNT'),
        'user': os.getenv('SNOW_USER'),
        'password': os.getenv('SNOW_PASSWORD'),
        'role': os.getenv('SNOW_ROLE', 'ACCOUNTADMIN'),
        'warehouse': os.getenv('SNOW_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOW_DATABASE', 'SNOWFLAKE_LEARNING_DB'),
        'schema': os.getenv('SNOW_SCHEMA', 'MON_SCHEMA')
    }
    
    # Validate required environment variables
    required_vars = ['SNOW_ACCOUNT', 'SNOW_USER', 'SNOW_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Create a .env file with your Snowflake credentials")
        sys.exit(1)
    
    print(f"🔧 Configuration:")
    print(f"   Kafka: {kafka_config['bootstrap_servers']} -> {kafka_config['topic']}")
    print(f"   Snowflake: {snowflake_config['account']} -> {snowflake_config['database']}.{snowflake_config['schema']}")
    
    consumer = OrderConsumer(kafka_config, snowflake_config)
    
    # Connect to both systems
    if not consumer.connect_kafka():
        sys.exit(1)
    
    if not consumer.connect_snowflake():
        sys.exit(1)
    
    try:
        consumer.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Consumer error: {e}")
        sys.exit(1)
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
