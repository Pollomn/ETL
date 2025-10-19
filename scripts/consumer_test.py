#!/usr/bin/env python3
"""
Consumer Kafka test sans Snowflake
"""
import json
import time
from kafka import KafkaConsumer

def main():
    print("🔍 Test consumer Kafka (sans Snowflake)...")
    
    try:
        consumer = KafkaConsumer(
            'orders_topic',
            bootstrap_servers='localhost:9092',
            group_id='test-kafka-only',
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=5000
        )
        
        print("✅ Consumer créé, attente des messages...")
        
        message_count = 0
        for message in consumer:
            print(f"📦 Message reçu: {message.value}")
            message_count += 1
            if message_count >= 3:
                break
        
        print(f"✅ Test terminé: {message_count} messages reçus")
        consumer.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
