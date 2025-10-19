# 📚 Documentation Complète - Pipeline Dropshipping

## 🎯 **Vue d'ensemble du projet**

Ce projet implémente un pipeline de données complet pour un site de dropshipping (vêtements) utilisant :
- **Génération de données** : Clients, produits, commandes
- **Streaming** : Apache Kafka/Redpanda pour les événements temps réel
- **Data Warehouse** : Snowflake pour le stockage et l'ETL
- **Monitoring** : Streamlit pour le dashboard
- **Validation** : Scripts automatisés de contrôle qualité

## 🏗️ **Architecture du Pipeline**

```
Data Generator → CSV Export → Kafka Producer → Redpanda → Kafka Consumer → Snowflake RAW → Stream → Task → Snowflake PROD → Streamlit Dashboard
```

### **Composants :**

1. **Data Generation** : Génération de données synthétiques
2. **Kafka Streaming** : Transport des événements en temps réel
3. **Snowflake ETL** : Transformation et stockage des données
4. **Monitoring** : Dashboard temps réel et validation

---

## 📋 **Prérequis et Installation**

### **1. Prérequis système**
```bash
# macOS avec Homebrew
brew install docker
brew install python3
brew install git

# Ou installation manuelle
# - Docker Desktop
# - Python 3.8+
# - Git
```

### **2. Installation des dépendances**
```bash
# Cloner le projet
git clone <repo-url>
cd "Projet final"

# Installer les dépendances Python
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync
```

### **3. Configuration Snowflake**
```bash
# Copier le template
cp .env.example .env

# Éditer .env avec vos credentials Snowflake
nano .env
```

**Variables d'environnement requises :**
```env
SNOW_ACCOUNT=your_account_here
SNOW_USER=your_username_here
SNOW_PASSWORD=your_password_here
SNOW_ROLE=ACCOUNTADMIN
SNOW_WAREHOUSE=mon_entrepot
SNOW_DATABASE=ma_base
SNOW_SCHEMA=mon_schema
```

---

## 🚀 **Guide d'Exécution Complet**

### **Étape 1 : Génération des données**
```bash
# Générer les données de base
make generate-data

# Ou manuellement
python scripts/export_seed.py --customers 1000 --products 200 --orders 5000 --seed 42
```

**Résultat :** Fichiers CSV créés dans `data/seed/`
- `customers.csv` : 1000 clients
- `inventory.csv` : 200 produits
- `orders.csv` : 5000 commandes

### **Étape 2 : Démarrage de l'infrastructure**
```bash
# Démarrer Redpanda (Kafka)
make docker-up

# Vérifier le statut
docker ps
docker exec redpanda rpk cluster info
```

**Résultat :** Redpanda disponible sur `localhost:9092`

### **Étape 3 : Configuration Snowflake**
```bash
# Exécuter les scripts SQL
bash snowflake/run_all.sh

# Ou manuellement avec Python
python -c "
import snowflake.connector
import os
from dotenv import load_dotenv
load_dotenv()

# Connexion et exécution des scripts
conn = snowflake.connector.connect(
    account=os.getenv('SNOW_ACCOUNT'),
    user=os.getenv('SNOW_USER'),
    password=os.getenv('SNOW_PASSWORD'),
    role=os.getenv('SNOW_ROLE'),
    warehouse=os.getenv('SNOW_WAREHOUSE'),
    database=os.getenv('SNOW_DATABASE'),
    schema=os.getenv('SNOW_SCHEMA')
)

# Exécuter chaque script SQL
for script in ['01_create_warehouse_db_schemas.sql', '02_create_tables.sql', '03_create_stream_and_task.sql']:
    with open(f'snowflake/{script}', 'r') as f:
        sql = f.read()
        for statement in sql.split(';'):
            if statement.strip():
                conn.cursor().execute(statement)
                print(f'✅ Exécuté: {script}')

conn.close()
"
```

**Résultat :** Tables Snowflake créées
- `mon_schema.orders_events` (RAW)
- `mon_schema.orders` (PROD)
- `mon_schema.customers` (PROD)
- `mon_schema.inventory` (PROD)

### **Étape 4 : Lancement du Consumer**
```bash
# Lancer le consumer en arrière-plan
python scripts/consumer_snowflake.py &

# Vérifier qu'il fonctionne
ps aux | grep consumer
```

**Résultat :** Consumer connecté à Kafka et Snowflake

### **Étape 5 : Production d'événements**
```bash
# Mode replay (fichier existant)
python scripts/producer.py --mode replay --rate 10

# Mode stream (génération continue)
python scripts/producer.py --mode stream --rate 5
```

**Résultat :** Événements `order_created` publiés sur `orders_topic`

### **Étape 6 : Monitoring**
```bash
# Lancer le dashboard Streamlit
streamlit run streamlit_monitor/app.py --server.port 8501

# Ou avec make
make monitor
```

**Résultat :** Dashboard accessible sur `http://localhost:8501`

### **Étape 7 : Validation**
```bash
# Exécuter les contrôles qualité
python scripts/validate.py

# Vérifier le rapport
cat reports/validate_report_*.json
```

**Résultat :** Rapport de validation JSON généré

---

## 🔧 **Commandes de Maintenance**

### **Gestion Docker**
```bash
# Démarrer Redpanda
make docker-up

# Arrêter Redpanda
make docker-down

# Vérifier les logs
docker logs redpanda

# Redémarrer proprement
make docker-down && make docker-up
```

### **Gestion des données**
```bash
# Nettoyer les données générées
rm -rf data/seed/*.csv

# Régénérer les données
make generate-data

# Vérifier les fichiers
ls -la data/seed/
```

### **Gestion Kafka**
```bash
# Lister les topics
docker exec redpanda rpk topic list

# Consommer des messages
docker exec redpanda rpk topic consume orders_topic --num 5

# Produire un message test
echo '{"test": "message"}' | docker exec -i redpanda rpk topic produce orders_topic

# Supprimer et recréer un topic
docker exec redpanda rpk topic delete orders_topic
docker exec redpanda rpk topic create orders_topic --partitions 3
```

### **Gestion Snowflake**
```bash
# Se connecter à Snowflake
snowsql -a <account> -u <user> -w <warehouse> -d <database> -s <schema>

# Exécuter des requêtes
snowsql -a <account> -u <user> -q "SELECT COUNT(*) FROM mon_schema.orders;"

# Vérifier les streams et tasks
snowsql -a <account> -u <user> -q "SHOW STREAMS IN SCHEMA mon_schema;"
snowsql -a <account> -u <user> -q "SHOW TASKS IN SCHEMA mon_schema;"
```

---

## 📊 **Monitoring et Debugging**

### **Vérification du pipeline complet**
```bash
# 1. Vérifier Redpanda
docker exec redpanda rpk cluster info

# 2. Vérifier les messages Kafka
docker exec redpanda rpk topic consume orders_topic --num 3

# 3. Vérifier Snowflake
python -c "
import snowflake.connector
import os
from dotenv import load_dotenv
load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv('SNOW_ACCOUNT'),
    user=os.getenv('SNOW_USER'),
    password=os.getenv('SNOW_PASSWORD'),
    role=os.getenv('SNOW_ROLE'),
    warehouse=os.getenv('SNOW_WAREHOUSE'),
    database=os.getenv('SNOW_DATABASE'),
    schema=os.getenv('SNOW_SCHEMA')
)

cursor = conn.cursor()

# Vérifier les événements bruts
cursor.execute('SELECT COUNT(*) FROM mon_schema.orders_events')
raw_count = cursor.fetchone()[0]
print(f'📦 Événements bruts: {raw_count}')

# Vérifier les commandes traitées
cursor.execute('SELECT COUNT(*) FROM mon_schema.orders')
orders_count = cursor.fetchone()[0]
print(f'📋 Commandes totales: {orders_count}')

conn.close()
"
```

### **Logs et debugging**
```bash
# Logs Redpanda
docker logs redpanda --tail 50

# Logs du consumer
python scripts/consumer_snowflake.py 2>&1 | tee consumer.log

# Test de connectivité Kafka
python -c "
from kafka import KafkaConsumer
consumer = KafkaConsumer('orders_topic', bootstrap_servers='localhost:9092', consumer_timeout_ms=5000)
print('✅ Kafka accessible')
consumer.close()
"
```

---

## 🏗️ **Architecture Détaillée des Composants**

### **1. Data Generator (`data_generator.py`)**

**Fonction :** Génération de données synthétiques réalistes

**Fonctions principales :**
```python
def generate_customers(n_customers=1000, seed=42):
    """Génère des clients avec données réalistes"""
    
def generate_inventory_data(n_products=200, seed=42):
    """Génère un catalogue de produits vêtements"""
    
def generate_orders(customers_df, inventory_df, n_orders=5000, seed=42):
    """Génère des commandes avec historique temporel"""
```

**Paramètres configurables :**
- Nombre de clients, produits, commandes
- Seed pour reproductibilité
- Catégories de produits
- Périodes temporelles

### **2. Export Script (`scripts/export_seed.py`)**

**Fonction :** Export des DataFrames en CSV avec formatage

**Fonctionnalités :**
- Formatage des dates en ISO 8601 UTC
- Prix à 2 décimales
- IDs cohérents
- Arguments CLI configurables

**Usage :**
```bash
python scripts/export_seed.py --customers 1000 --products 200 --orders 5000 --seed 42
```

### **3. Kafka Producer (`scripts/producer.py`)**

**Fonction :** Publication d'événements sur le topic Kafka

**Modes d'opération :**
- **Replay** : Lit `orders.csv` et publie chaque ligne
- **Stream** : Génère des événements aléatoires en continu

**Configuration :**
```python
KAFKA_CONFIG = {
    'bootstrap_servers': 'localhost:9092',
    'topic': 'orders_topic'
}
```

**Usage :**
```bash
# Mode replay
python scripts/producer.py --mode replay --rate 10

# Mode stream
python scripts/producer.py --mode stream --rate 5
```

### **4. Kafka Consumer (`scripts/consumer_snowflake.py`)**

**Fonction :** Consommation des événements et insertion dans Snowflake

**Architecture :**
- Connexion Kafka avec `kafka-python-ng`
- Connexion Snowflake avec `snowflake-connector-python`
- Traitement par batch pour performance
- Gestion d'erreurs robuste

**Configuration :**
```python
# Kafka
bootstrap_servers: localhost:9092
group_id: snowflake-consumer-group
auto_offset_reset: latest

# Snowflake
warehouse: mon_entrepot
database: ma_base
schema: mon_schema
```

### **5. Snowflake Schema (`snowflake/`)**

**Structure des tables :**

#### **RAW Schema (`mon_schema.orders_events`)**
```sql
CREATE TABLE mon_schema.orders_events (
    event_id STRING,
    event_type STRING,
    payload VARIANT,
    created_at TIMESTAMP_NTZ
);
```

#### **PROD Schema**
```sql
-- Commandes
CREATE TABLE mon_schema.orders (
    id STRING PRIMARY KEY,
    product_id STRING,
    customer_id STRING,
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    sold_at TIMESTAMP_NTZ,
    ingested_at TIMESTAMP_NTZ
);

-- Clients
CREATE TABLE mon_schema.customers (
    id STRING PRIMARY KEY,
    name STRING,
    email STRING,
    city STRING,
    country STRING
);

-- Inventaire
CREATE TABLE mon_schema.inventory (
    id STRING PRIMARY KEY,
    product_name STRING,
    category STRING,
    price DECIMAL(10,2),
    stock_quantity INTEGER
);
```

### **6. Stream et Task (`snowflake/03_create_stream_and_task.sql`)**

**Stream :** Surveillance des changements sur `orders_events`
```sql
CREATE STREAM mon_schema.orders_stream ON TABLE mon_schema.orders_events;
```

**Task :** ETL automatisé toutes les minutes
```sql
CREATE TASK mon_schema.ingest_orders_task
WAREHOUSE = mon_entrepot
SCHEDULE = '1 minute'
WHEN SYSTEM$STREAM_HAS_DATA('mon_schema.orders_stream')
AS
MERGE INTO mon_schema.orders AS target
USING mon_schema.orders_stream AS source
ON target.id = source.payload:order.id::STRING
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```

### **7. Streamlit Dashboard (`streamlit_monitor/app.py`)**

**Fonction :** Interface de monitoring temps réel

**KPIs affichés :**
- Total commandes
- CA total
- Commandes dernières 24h
- Top 5 produits (volume + CA)
- 20 dernières commandes

**Architecture :**
```python
def get_kpis():
    """Récupère les KPIs principaux"""
    
def get_top_products():
    """Récupère le top 5 des produits"""
    
def get_recent_orders():
    """Récupère les 20 dernières commandes"""
```

### **8. Validation Script (`scripts/validate.py`)**

**Fonction :** Contrôles qualité automatisés

**Contrôles effectués :**
- Comparaison raw vs prod
- Détection de doublons
- Qualité des données
- Activité récente
- Statut des tasks

**Rapport généré :**
```json
{
  "timestamp": "2025-10-19T00:00:00Z",
  "checks": {
    "raw_vs_prod_counts": {"status": "PASS"},
    "duplicates": {"status": "PASS"},
    "data_quality": {"status": "PASS"},
    "recent_activity": {"status": "PASS"},
    "task_status": {"status": "PASS"}
  },
  "status": "PASS"
}
```

---

## 🐛 **Troubleshooting Complet**

### **Problème 1 : Consumer ne traite pas les messages**

**Symptômes :**
- Consumer se lance puis se ferme immédiatement
- "0 events processed" dans les logs
- Messages présents dans Kafka mais non traités

**Diagnostic :**
```bash
# Vérifier les messages dans Kafka
docker exec redpanda rpk topic consume orders_topic --num 5

# Tester la connectivité
python -c "
from kafka import KafkaConsumer
consumer = KafkaConsumer('orders_topic', bootstrap_servers='localhost:9092', consumer_timeout_ms=5000)
for msg in consumer:
    print(f'Message: {msg.value}')
    break
"
```

**Solutions :**
1. **Changer l'offset** : `auto_offset_reset='latest'`
2. **Timeout approprié** : `consumer_timeout_ms=5000`
3. **Groupe différent** : `group_id='new-group'`
4. **Recréer le topic** : `docker exec redpanda rpk topic delete orders_topic`

### **Problème 2 : Erreurs Snowflake**

**Symptômes :**
- `Schema 'MA_BASE.RAW' does not exist`
- `Role 'POLLOM' specified does not exist`
- Connexion échoue

**Solutions :**
```bash
# Vérifier les credentials
cat .env

# Tester la connexion
python -c "
import snowflake.connector
import os
from dotenv import load_dotenv
load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv('SNOW_ACCOUNT'),
    user=os.getenv('SNOW_USER'),
    password=os.getenv('SNOW_PASSWORD'),
    role=os.getenv('SNOW_ROLE'),
    warehouse=os.getenv('SNOW_WAREHOUSE'),
    database=os.getenv('SNOW_DATABASE'),
    schema=os.getenv('SNOW_SCHEMA')
)
print('✅ Connexion Snowflake OK')
conn.close()
"
```

### **Problème 3 : Redpanda ne démarre pas**

**Symptômes :**
- `Cannot connect to the Docker daemon`
- `Conflict. The container name "/redpanda" is already in use`

**Solutions :**
```bash
# Démarrer Docker Desktop
open -a Docker

# Nettoyer les containers
docker stop redpanda
docker rm redpanda

# Redémarrer proprement
make docker-down
make docker-up
```

### **Problème 4 : Dashboard Streamlit erreurs**

**Symptômes :**
- `Value of 'x' is not the name of a column`
- `SQL compilation error: invalid identifier`

**Solutions :**
1. **Vérifier les noms de colonnes** : Snowflake utilise des majuscules
2. **Vérifier les schémas** : `mon_schema` au lieu de `prod`
3. **Tester les requêtes** : Exécuter directement dans Snowsight

---

## 📈 **Métriques et Performance**

### **Métriques Kafka**
```bash
# Statistiques du topic
docker exec redpanda rpk topic describe orders_topic

# Messages par partition
docker exec redpanda rpk topic consume orders_topic --num 10 --print-keys
```

### **Métriques Snowflake**
```sql
-- Taille des tables
SELECT 
    table_name,
    row_count,
    bytes
FROM information_schema.tables 
WHERE table_schema = 'MON_SCHEMA';

-- Performance des queries
SELECT 
    query_id,
    query_text,
    execution_time,
    bytes_scanned
FROM snowflake.account_usage.query_history 
WHERE start_time > current_timestamp - interval '1 hour'
ORDER BY start_time DESC;
```

### **Métriques du Pipeline**
```bash
# Temps de traitement
time python scripts/producer.py --mode replay --rate 100

# Throughput
docker exec redpanda rpk topic consume orders_topic --num 1000 | wc -l

# Latence end-to-end
python scripts/validate.py
```

---

## 🔒 **Sécurité et Bonnes Pratiques**

### **Gestion des secrets**
```bash
# Ne jamais committer .env
echo ".env" >> .gitignore

# Utiliser des variables d'environnement
export SNOW_PASSWORD="secret"
python scripts/consumer_snowflake.py
```

### **Validation des données**
```python
# Validation des schémas
import pandas as pd
from pydantic import BaseModel

class OrderEvent(BaseModel):
    event_type: str
    order: dict
    timestamp: str

# Validation avant insertion
def validate_event(event_data):
    try:
        OrderEvent(**event_data)
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False
```

### **Gestion des erreurs**
```python
# Retry logic
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))
            return wrapper
        return decorator
```

---

## 🚀 **Déploiement et Production**

### **Configuration Production**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  redpanda:
    image: docker.redpanda.com/redpandadata/redpanda:latest
    command:
      - redpanda
      - start
      - --kafka-addr
      - internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr
      - internal://redpanda:9092,external://localhost:19092
      - --pandaproxy-addr
      - internal://0.0.0.0:8082,external://0.0.0.0:18082
      - --advertise-pandaproxy-addr
      - internal://redpanda:8082,external://localhost:18082
      - --schema-registry-addr
      - internal://0.0.0.0:8081,external://0.0.0.0:18081
    ports:
      - "19092:19092"
      - "18081:18081"
      - "18082:18082"
    volumes:
      - redpanda_data:/var/lib/redpanda/data
```

### **Monitoring Production**
```python
# Health checks
def check_kafka_health():
    try:
        consumer = KafkaConsumer(bootstrap_servers='localhost:9092', consumer_timeout_ms=1000)
        consumer.close()
        return True
    except:
        return False

def check_snowflake_health():
    try:
        conn = snowflake.connector.connect(**snowflake_config)
        conn.close()
        return True
    except:
        return False
```

### **Scaling**
```bash
# Multiple consumers
python scripts/consumer_snowflake.py --group-id consumer-1 &
python scripts/consumer_snowflake.py --group-id consumer-2 &

# Multiple producers
python scripts/producer.py --mode stream --rate 100 &
python scripts/producer.py --mode stream --rate 100 &
```

---

## 📚 **Références et Ressources**

### **Documentation Officielle**
- [Apache Kafka](https://kafka.apache.org/documentation/)
- [Redpanda](https://docs.redpanda.com/)
- [Snowflake](https://docs.snowflake.com/)
- [Streamlit](https://docs.streamlit.io/)

### **Libraries Python**
- `kafka-python-ng` : Client Kafka
- `snowflake-connector-python` : Client Snowflake
- `streamlit` : Dashboard web
- `pandas` : Manipulation de données
- `faker` : Génération de données

### **Outils de Debugging**
```bash
# Kafka tools
docker exec redpanda rpk topic list
docker exec redpanda rpk topic consume orders_topic --num 10

# Snowflake tools
snowsql -a <account> -u <user> -q "SHOW TABLES;"

# Python debugging
python -m pdb scripts/consumer_snowflake.py
```

---

## 🎯 **Checklist de Validation Finale**

### **✅ Infrastructure**
- [ ] Docker Desktop démarré
- [ ] Redpanda container actif et healthy
- [ ] Topic `orders_topic` créé avec 3 partitions
- [ ] Connexion Kafka fonctionnelle

### **✅ Snowflake**
- [ ] Connexion Snowflake réussie
- [ ] Tables créées (orders_events, orders, customers, inventory)
- [ ] Stream et Task créés et actifs
- [ ] Données de test insérées

### **✅ Pipeline**
- [ ] Consumer connecté et en attente
- [ ] Producer génère des événements
- [ ] Messages traités dans Snowflake
- [ ] Dashboard Streamlit fonctionnel

### **✅ Validation**
- [ ] Script de validation exécuté
- [ ] Rapport JSON généré
- [ ] Aucune erreur critique
- [ ] Métriques cohérentes

### **✅ Documentation**
- [ ] README.md complet
- [ ] Scripts documentés
- [ ] Configuration expliquée
- [ ] Troubleshooting couvert

---

## 🎉 **Conclusion**

Ce pipeline de dropshipping est un exemple complet d'architecture de données moderne intégrant :

- **Génération de données** réalistes et reproductibles
- **Streaming temps réel** avec Kafka/Redpanda
- **Data Warehouse** avec Snowflake et ETL automatisé
- **Monitoring** avec dashboard Streamlit
- **Validation** automatisée et rapports

Le projet respecte les bonnes pratiques de l'industrie et peut servir de base pour des implémentations production plus complexes.

**Pipeline 100% fonctionnel et documenté !** 🚀
