# Pipeline Architecture Diagram

## Flux de données complet

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Generator │    │   CSV Export     │    │  Kafka Producer │
│                 │    │                 │    │                 │
│ • generate_     │───▶│ • customers.csv │───▶│ • Mode: replay   │
│   customers()   │    │ • inventory.csv │    │   / stream       │
│ • generate_     │    │ • orders.csv    │    │ • Rate limiting  │
│   inventory()   │    │                 │    │ • JSON events    │
│ • generate_     │    │                 │    │                 │
│   orders()      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redpanda      │    │ Kafka Consumer │    │   Snowflake     │
│   (Kafka)       │    │                │    │   RAW Schema    │
│                 │    │ • orders_topic │    │                 │
│ • Topic:        │◀───│ • Batch insert │───▶│ • orders_events │
│   orders_topic  │    │ • Error handle │    │ • VARIANT JSON  │
│ • Port: 9092    │    │ • Snowflake    │    │ • Timestamps    │
│                 │    │   connector    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Snowflake     │    │   Snowflake     │    │   Snowflake     │
│   STREAM        │    │   TASK          │    │   PROD Schema   │
│                 │    │                 │    │                 │
│ • CDC capture   │───▶│ • Cron: 1 min   │───▶│ • orders       │
│ • New events    │    │ • MERGE logic   │    │ • customers    │
│ • Metadata      │    │ • Upsert        │    │ • inventory    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │   Streamlit     │    │   Monitoring   │
│                 │    │   Dashboard     │    │                 │
│ • Quality       │    │                 │    │ • KPIs real-time│
│   checks        │    │ • KPI cards     │    │ • Top products │
│ • Duplicates    │    │ • Charts        │    │ • Recent orders│
│ • Data quality  │    │ • Tables        │    │ • Trends       │
│ • JSON report   │    │ • Auto-refresh  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Composants techniques

### 1. Génération de données
- **Script** : `scripts/export_seed.py`
- **Fonctions** : `generate_customers()`, `generate_inventory()`, `generate_orders()`
- **Format** : CSV avec timestamps ISO 8601 UTC
- **Volume** : 1000 clients, 200 produits, 5000 commandes (par défaut)

### 2. Infrastructure Kafka
- **Broker** : Redpanda (Kafka-compatible)
- **Topic** : `orders_topic`
- **Port** : 9092 (external), 29092 (internal)
- **Docker** : `docker-compose.yml`

### 3. Producer Kafka
- **Script** : `scripts/producer.py`
- **Modes** : replay (CSV) / stream (continu)
- **Rate limiting** : Configurable (events/sec)
- **Format** : JSON avec metadata

### 4. Consumer Snowflake
- **Script** : `scripts/consumer_snowflake.py`
- **Batch processing** : 10 messages ou 5s timeout
- **Table** : `raw.orders_events`
- **Format** : VARIANT JSON + timestamps

### 5. Infrastructure Snowflake
- **Warehouse** : COMPUTE_WH (XSMALL)
- **Database** : DROPSHIPPING_DB
- **Schémas** : RAW, STAGING, PROD
- **Tables** : orders_events, orders, customers, inventory

### 6. ETL automatisé
- **Stream** : `raw.orders_stream` (CDC)
- **Task** : `prod.ingest_orders_task` (cron 1 min)
- **Logic** : MERGE upsert vers prod.orders
- **Déclencheur** : `SYSTEM$STREAM_HAS_DATA()`

### 7. Validation
- **Script** : `scripts/validate.py`
- **Checks** : raw vs prod counts, duplicates, data quality
- **Rapport** : JSON avec timestamp
- **Exit codes** : 0 (success), 1 (failures)

### 8. Dashboard
- **Framework** : Streamlit
- **Script** : `streamlit_monitor/app.py`
- **Fonctionnalités** : KPIs, charts, tables, auto-refresh
- **Visualisations** : Plotly (bar, line charts)

## Flux de données détaillé

### Phase 1 : Génération
```
Python Script → DataFrame → CSV Files
```

### Phase 2 : Streaming
```
CSV → Producer → Kafka → Consumer → Snowflake RAW
```

### Phase 3 : ETL
```
RAW → Stream → Task → PROD
```

### Phase 4 : Monitoring
```
PROD → Dashboard → KPIs/Charts
```

## Configuration

### Variables d'environnement
```bash
# Snowflake
SNOW_ACCOUNT=your_account
SNOW_USER=your_user
SNOW_PASSWORD=your_password
SNOW_ROLE=ACCOUNTADMIN
SNOW_WAREHOUSE=COMPUTE_WH
SNOW_DATABASE=DROPSHIPPING_DB
SNOW_SCHEMA=RAW

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=orders_topic
```

### Commandes principales
```bash
# Setup complet
make all

# Génération données
make generate-data

# Infrastructure
make docker-up

# Snowflake
bash snowflake/run_all.sh

# Pipeline
python scripts/producer.py --mode replay --rate 10
python scripts/consumer_snowflake.py

# Validation
make validate

# Monitoring
make monitor
```

## Points d'intégration

### 1. Kafka ↔ Snowflake
- **Connecteur** : `snowflake-connector-python`
- **Authentification** : Variables d'environnement
- **Gestion d'erreurs** : Retry logic, logging

### 2. Snowflake RAW ↔ PROD
- **Stream** : Capture des changements (CDC)
- **Task** : Transformation et chargement
- **Scheduling** : Cron 1 minute

### 3. PROD ↔ Dashboard
- **Connexion** : Snowflake connector
- **Requêtes** : SQL optimisées avec index
- **Refresh** : Auto-refresh 30s

## Monitoring et observabilité

### Métriques clés
- **Throughput** : Events/sec, Orders/min
- **Latence** : Kafka → Snowflake, RAW → PROD
- **Qualité** : Duplicates, NULLs, anomalies
- **Performance** : Query time, task execution

### Logs
- **Producer** : Events sent, rate, errors
- **Consumer** : Messages processed, batch size, errors
- **Snowflake** : Task execution, query performance
- **Dashboard** : Connection status, query results

### Alertes
- **Kafka** : Consumer lag, connection failures
- **Snowflake** : Task failures, data quality issues
- **Dashboard** : Connection timeouts, empty results
