#!/usr/bin/env python3
"""
Consumer Kafka qui fonctionne vraiment
"""
import json
from kafka import KafkaConsumer

def main():
    print("🔍 Consumer Kafka fonctionnel...")
    
    consumer = KafkaConsumer(
        'orders_topic',
        bootstrap_servers='localhost:9092',
        group_id='working-group',
        auto_offset_reset='latest',  # Commencer par les nouveaux messages
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=3000  # 3 secondes seulement
    )
    
    print("✅ Consumer créé, lecture des messages...")
    
    try:
        for message in consumer:
            print(f"📦 Message: {message.value}")
            break  # Un seul message pour le test
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        consumer.close()
        print("✅ Consumer fermé")

if __name__ == "__main__":
    main()
