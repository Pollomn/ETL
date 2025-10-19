# 🖥️ Référence Complète des Commandes

## 📋 **Commandes de Base du Pipeline**

### **1. Installation et Configuration**

```bash
# Cloner le projet
git clone <repo-url>
cd "Projet final"

# Installer les dépendances
pip install -r requirements.txt

# Ou avec uv (recommandé)
uv sync

# Configuration Snowflake
cp .env.example .env
nano .env  # Éditer avec vos credentials
```

### **2. Génération des Données**

```bash
# Génération standard (1000 clients, 200 produits, 5000 commandes)
make generate-data

# Génération personnalisée
python scripts/export_seed.py --customers 2000 --products 500 --orders 10000 --seed 123

# Vérification des fichiers générés
ls -la data/seed/
head -5 data/seed/orders.csv
```

**Paramètres disponibles :**
- `--customers N` : Nombre de clients (défaut: 1000)
- `--products M` : Nombre de produits (défaut: 200)
- `--orders K` : Nombre de commandes (défaut: 5000)
- `--seed S` : Seed pour reproductibilité (défaut: 42)
- `--output DIR` : Dossier de sortie (défaut: data/seed)

### **3. Infrastructure Docker**

```bash
# Démarrer Redpanda
make docker-up

# Vérifier le statut
docker ps
docker logs redpanda

# Arrêter Redpanda
make docker-down

# Redémarrer proprement
make docker-down && make docker-up
```

**Vérifications :**
```bash
# Santé du cluster
docker exec redpanda rpk cluster info

# Liste des topics
docker exec redpanda rpk topic list

# Détails du topic
docker exec redpanda rpk topic describe orders_topic
```

### **4. Configuration Snowflake**

```bash
# Exécution automatique des scripts SQL
bash snowflake/run_all.sh

# Ou exécution manuelle
snowsql -a <account> -u <user> -w <warehouse> -d <database> -s <schema> -f snowflake/01_create_warehouse_db_schemas.sql
snowsql -a <account> -u <user> -w <warehouse> -d <database> -s <schema> -f snowflake/02_create_tables.sql
snowsql -a <account> -u <user> -w <warehouse> -d <database> -s <schema> -f snowflake/03_create_stream_and_task.sql
snowsql -a <account> -u <user> -w <warehouse> -d <database> -s <schema> -f snowflake/04_validate_ingestion.sql
```

**Vérifications Snowflake :**
```bash
# Test de connexion
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

# Vérifier les tables
snowsql -a <account> -u <user> -q "SHOW TABLES IN SCHEMA mon_schema;"

# Vérifier les streams et tasks
snowsql -a <account> -u <user> -q "SHOW STREAMS IN SCHEMA mon_schema;"
snowsql -a <account> -u <user> -q "SHOW TASKS IN SCHEMA mon_schema;"
```

---

## 🚀 **Commandes du Pipeline de Streaming**

### **1. Consumer Kafka → Snowflake**

```bash
# Lancement du consumer
python scripts/consumer_snowflake.py

# Lancement en arrière-plan
python scripts/consumer_snowflake.py &

# Vérifier qu'il fonctionne
ps aux | grep consumer

# Arrêter le consumer
pkill -f consumer_snowflake.py
```

**Configuration du consumer :**
- **Groupe** : `snowflake-consumer-group`
- **Offset** : `latest` (nouveaux messages)
- **Timeout** : 5 secondes
- **Batch size** : 10 messages

### **2. Producer Kafka**

#### **Mode Replay (fichier existant)**
```bash
# Replay standard (10 msg/s)
python scripts/producer.py --mode replay --rate 10

# Replay rapide (50 msg/s)
python scripts/producer.py --mode replay --rate 50

# Replay lent (1 msg/s)
python scripts/producer.py --mode replay --rate 1
```

#### **Mode Stream (génération continue)**
```bash
# Stream standard (5 msg/s)
python scripts/producer.py --mode stream --rate 5

# Stream rapide (20 msg/s)
python scripts/producer.py --mode stream --rate 20

# Stream lent (1 msg/s)
python scripts/producer.py --mode stream --rate 1
```

**Paramètres disponibles :**
- `--mode {replay,stream}` : Mode d'opération
- `--rate N` : Messages par seconde
- `--file PATH` : Fichier CSV pour mode replay (défaut: data/seed/orders.csv)

### **3. Tests Kafka**

```bash
# Produire un message test
echo '{"event_type": "order_created", "order": {"id": "TEST_001", "product_id": "PROD_001", "customer_id": "CUST_001", "quantity": 1, "unit_price": 29.99, "sold_at": "2024-01-01T12:00:00Z"}}' | docker exec -i redpanda rpk topic produce orders_topic

# Consommer des messages
docker exec redpanda rpk topic consume orders_topic --num 5

# Consommer en continu
docker exec redpanda rpk topic consume orders_topic

# Vérifier les offsets
docker exec redpanda rpk topic describe orders_topic
```

---

## 📊 **Commandes de Monitoring**

### **1. Dashboard Streamlit**

```bash
# Lancement standard
streamlit run streamlit_monitor/app.py --server.port 8501

# Ou avec make
make monitor

# Lancement en arrière-plan
streamlit run streamlit_monitor/app.py --server.port 8501 &

# Arrêter Streamlit
pkill -f streamlit
```

**Accès :** `http://localhost:8501`

### **2. Validation du Pipeline**

```bash
# Validation complète
python scripts/validate.py

# Ou avec make
make validate

# Vérifier le rapport
cat reports/validate_report_*.json

# Validation avec sortie détaillée
python scripts/validate.py --verbose
```

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

### **3. Vérifications Snowflake**

```bash
# Comptes des tables
snowsql -a <account> -u <user> -q "SELECT COUNT(*) FROM mon_schema.orders_events;"
snowsql -a <account> -u <user> -q "SELECT COUNT(*) FROM mon_schema.orders;"

# Dernière activité
snowsql -a <account> -u <user> -q "SELECT MAX(created_at) FROM mon_schema.orders_events;"
snowsql -a <account> -u <user> -q "SELECT MAX(ingested_at) FROM mon_schema.orders;"

# Statut des tasks
snowsql -a <account> -u <user> -q "SHOW TASKS IN SCHEMA mon_schema;"

# Exécution manuelle de la task
snowsql -a <account> -u <user> -q "ALTER TASK mon_schema.ingest_orders_task EXECUTE;"
```

---

## 🔧 **Commandes de Maintenance**

### **1. Gestion Docker**

```bash
# Statut des containers
docker ps
docker ps -a

# Logs Redpanda
docker logs redpanda
docker logs redpanda --tail 50
docker logs redpanda --follow

# Redémarrer Redpanda
docker restart redpanda

# Nettoyer les containers
docker stop redpanda
docker rm redpanda
docker system prune -f
```

### **2. Gestion des Données**

```bash
# Nettoyer les données générées
rm -rf data/seed/*.csv

# Régénérer les données
make generate-data

# Vérifier les fichiers
ls -la data/seed/
wc -l data/seed/*.csv

# Nettoyer les rapports
rm -rf reports/*.json
```

### **3. Gestion Kafka**

```bash
# Lister les topics
docker exec redpanda rpk topic list

# Supprimer un topic
docker exec redpanda rpk topic delete orders_topic

# Recréer un topic
docker exec redpanda rpk topic create orders_topic --partitions 3

# Vider un topic (supprimer et recréer)
docker exec redpanda rpk topic delete orders_topic
docker exec redpanda rpk topic create orders_topic --partitions 3

# Consommer depuis le début
docker exec redpanda rpk topic consume orders_topic --offset start --num 10

# Consommer depuis la fin
docker exec redpanda rpk topic consume orders_topic --offset end --num 10
```

### **4. Gestion des Processus**

```bash
# Lister les processus Python
ps aux | grep python

# Lister les consumers
ps aux | grep consumer

# Tuer tous les consumers
pkill -f consumer

# Tuer tous les producers
pkill -f producer

# Tuer Streamlit
pkill -f streamlit

# Tuer tous les processus du pipeline
pkill -f "consumer_snowflake.py"
pkill -f "producer.py"
pkill -f "streamlit"
```

---

## 🐛 **Commandes de Debugging**

### **1. Tests de Connectivité**

```bash
# Test Kafka
python -c "
from kafka import KafkaConsumer
consumer = KafkaConsumer('orders_topic', bootstrap_servers='localhost:9092', consumer_timeout_ms=5000)
print('✅ Kafka accessible')
consumer.close()
"

# Test Snowflake
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
print('✅ Snowflake accessible')
conn.close()
"
```

### **2. Tests de Performance**

```bash
# Test de throughput Kafka
time python scripts/producer.py --mode stream --rate 100

# Test de latence
time python scripts/consumer_snowflake.py

# Test de validation
time python scripts/validate.py
```

### **3. Logs et Monitoring**

```bash
# Logs Redpanda en temps réel
docker logs redpanda --follow

# Logs du consumer
python scripts/consumer_snowflake.py 2>&1 | tee consumer.log

# Logs du producer
python scripts/producer.py --mode stream --rate 10 2>&1 | tee producer.log

# Monitoring des ressources
docker stats redpanda
```

---

## 🚀 **Commandes de Déploiement**

### **1. Pipeline Complet**

```bash
# Déploiement complet
make all

# Ou étape par étape
make install
make generate-data
make docker-up
python scripts/consumer_snowflake.py &
python scripts/producer.py --mode stream --rate 10 &
make monitor
```

### **2. Tests de Validation**

```bash
# Test end-to-end
python scripts/validate.py

# Test de cohérence
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

# Vérifier la cohérence
if raw_count > 0 and orders_count > 0:
    print('✅ Pipeline fonctionnel')
else:
    print('❌ Pipeline non fonctionnel')

conn.close()
"
```

### **3. Nettoyage et Reset**

```bash
# Reset complet
make clean
make docker-down
rm -rf data/seed/*.csv
rm -rf reports/*.json

# Redéploiement
make all
```

---

## 📚 **Commandes de Documentation**

### **1. Génération de Documentation**

```bash
# Vérifier la structure
tree -I '__pycache__|*.pyc|.git'

# Compter les lignes de code
find . -name "*.py" -exec wc -l {} + | tail -1

# Vérifier les dépendances
pip list | grep -E "(kafka|snowflake|streamlit|pandas|faker)"
```

### **2. Tests de Code**

```bash
# Linting
ruff check .
black --check .

# Tests unitaires (si disponibles)
python -m pytest tests/

# Vérification des imports
python -c "import scripts.consumer_snowflake; import scripts.producer; import scripts.validate"
```

---

## 🎯 **Commandes de Production**

### **1. Monitoring Continu**

```bash
# Script de monitoring
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    docker exec redpanda rpk cluster info
    python scripts/validate.py
    sleep 60
done
```

### **2. Backup et Restore**

```bash
# Backup des données
cp -r data/seed/ backup/data_$(date +%Y%m%d)/

# Backup des rapports
cp -r reports/ backup/reports_$(date +%Y%m%d)/

# Restore
cp -r backup/data_20241019/* data/seed/
```

### **3. Scaling**

```bash
# Multiple consumers
python scripts/consumer_snowflake.py --group-id consumer-1 &
python scripts/consumer_snowflake.py --group-id consumer-2 &

# Multiple producers
python scripts/producer.py --mode stream --rate 50 &
python scripts/producer.py --mode stream --rate 50 &
```

---

## 🎉 **Résumé des Commandes Essentielles**

### **Démarrage Rapide**
```bash
# 1. Installation
pip install -r requirements.txt
cp .env.example .env  # Éditer avec vos credentials

# 2. Génération des données
make generate-data

# 3. Infrastructure
make docker-up

# 4. Consumer
python scripts/consumer_snowflake.py &

# 5. Producer
python scripts/producer.py --mode stream --rate 10 &

# 6. Monitoring
make monitor
```

### **Vérification**
```bash
# Vérifier Kafka
docker exec redpanda rpk topic consume orders_topic --num 3

# Vérifier Snowflake
python scripts/validate.py

# Vérifier le dashboard
curl http://localhost:8501
```

### **Nettoyage**
```bash
# Arrêter tout
pkill -f consumer
pkill -f producer
pkill -f streamlit
make docker-down

# Nettoyer
make clean
```

**Pipeline 100% fonctionnel avec ces commandes !** 🚀
