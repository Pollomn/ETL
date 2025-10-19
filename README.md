# 🛒 Dropshipping Pipeline

Un pipeline ETL complet pour un site de dropshipping vêtements, utilisant Kafka/Redpanda pour le streaming, Snowflake pour le stockage et l'analyse, et Streamlit pour le monitoring en temps réel.

## 🏗️ Architecture

```
Data Generator → CSV Export → Kafka Producer → Redpanda → Consumer → Snowflake RAW → Stream → Task → PROD → Streamlit Dashboard
```

### Composants

- **Génération de données** : Scripts Python pour créer des données réalistes (clients, produits, commandes)
- **Streaming** : Redpanda (Kafka-compatible) pour la gestion des événements en temps réel
- **Stockage** : Snowflake avec schémas RAW, STAGING, PROD
- **ETL automatisé** : Streams et Tasks Snowflake pour l'ingestion automatique
- **Monitoring** : Dashboard Streamlit avec KPIs et visualisations

## 🚀 Installation rapide

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- SnowSQL (pour Snowflake)
- uv (gestionnaire de dépendances Python)

### Installation

```bash
# 1. Cloner le repo
git clone <repo-url>
cd dropshipping-pipeline

# 2. Installer les dépendances
make install

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials Snowflake

# 4. Setup complet
make all
```

## 📋 Workflow d'exécution

### 1. Génération des données

```bash
# Générer les données de test
make generate-data

# Ou avec paramètres personnalisés
python scripts/export_seed.py --customers 1000 --products 200 --orders 5000 --seed 42
```

### 2. Infrastructure Kafka

```bash
# Démarrer Redpanda
make docker-up

# Vérifier que Kafka est disponible
docker ps
```

### 3. Configuration Snowflake

```bash
# Exécuter les scripts SQL
bash snowflake/run_all.sh
```

### 4. Pipeline de streaming

```bash
# Terminal 1: Producer (mode replay)
python scripts/producer.py --mode replay --rate 10

# Terminal 2: Consumer
python scripts/consumer_snowflake.py

# Terminal 3: Validation
python scripts/validate.py
```

### 5. Monitoring

```bash
# Dashboard Streamlit
make monitor
# Ou directement: streamlit run streamlit_monitor/app.py
```

## 🔧 Configuration

### Variables d'environnement (.env)

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

### Structure des données

#### Clients (customers.csv)
- `customer_id`, `name`, `email`, `city`, `channel`

#### Produits (inventory.csv)
- `product_id`, `product_name`, `category`, `unit_price`, `stock_quantity`

#### Commandes (orders.csv)
- `id`, `product_id`, `customer_id`, `quantity`, `unit_price`, `sold_at`

## 📊 Monitoring et validation

### Dashboard Streamlit

Le dashboard affiche :
- **KPIs** : Total commandes, CA, clients uniques, produits uniques
- **Top produits** : Par volume et chiffre d'affaires
- **Commandes récentes** : 20 dernières commandes
- **Tendances** : Graphiques des commandes et revenus quotidiens

### Validation automatique

```bash
# Vérifier la qualité des données
make validate

# Le script génère un rapport JSON dans reports/
```

## 🧪 Tests rapides

### Vérifier Kafka

```bash
# Lister les topics
docker exec -it redpanda rpk topic list

# Consommer les messages
docker exec -it redpanda rpk topic consume orders_topic
```

### Vérifier Snowflake

```sql
-- Compter les événements
SELECT COUNT(*) FROM raw.orders_events;

-- Compter les commandes
SELECT COUNT(*) FROM prod.orders;

-- Vérifier la task
SHOW TASKS IN SCHEMA prod;
```

## 📁 Structure du projet

```
/
├── data/seed/                    # CSV exportés
├── docker/                       # Configuration Docker
├── scripts/                      # Scripts Python
│   ├── export_seed.py           # Génération données
│   ├── producer.py              # Producer Kafka
│   ├── consumer_snowflake.py    # Consumer Snowflake
│   └── validate.py              # Validation qualité
├── snowflake/                    # Scripts SQL
│   ├── 01_create_warehouse_db_schemas.sql
│   ├── 02_create_tables.sql
│   ├── 03_create_stream_and_task.sql
│   ├── 04_validate_ingestion.sql
│   └── run_all.sh               # Exécution séquentielle
├── streamlit_monitor/            # Dashboard
├── reports/                      # Rapports validation
├── docs/                         # Documentation
└── .env.example                  # Template configuration
```

## 🚨 Dépannage

### Erreur de connexion Snowflake
- Vérifier les credentials dans `.env`
- Tester la connexion : `snowsql -a $SNOW_ACCOUNT -u $SNOW_USER`

### Kafka non accessible
- Vérifier que Redpanda est démarré : `docker ps`
- Tester la connexion : `docker exec -it redpanda rpk cluster health`

### Données manquantes
- Vérifier que les scripts SQL ont été exécutés
- Vérifier que le consumer fonctionne
- Vérifier que la task Snowflake est active

## 📈 Performance

### Recommandations

- **Warehouse Snowflake** : XSMALL pour le développement, SMALL+ pour la production
- **Rate limiting** : Ajuster `--rate` selon la capacité de traitement
- **Batch size** : Modifier la taille des batches dans le consumer

### Monitoring

- **Snowsight** : Interface web Snowflake pour les requêtes
- **Streamlit** : Dashboard temps réel
- **Logs** : Vérifier les logs des scripts pour les erreurs

## 🔄 Modes de fonctionnement

### Mode Replay
```bash
python scripts/producer.py --mode replay --file data/seed/orders.csv --rate 10
```
Rejoue les commandes depuis un fichier CSV à un rythme configurable.

### Mode Stream
```bash
python scripts/producer.py --mode stream --rate 5
```
Génère continuellement de nouvelles commandes aléatoires.

## 📝 Logs et rapports

- **Logs** : Affichés dans la console des scripts
- **Rapports** : `reports/validate_report_TIMESTAMP.json`
- **Dashboard** : Interface web Streamlit

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
1. Vérifier la documentation
2. Consulter les logs d'erreur
3. Tester les composants individuellement
4. Ouvrir une issue sur GitHub
