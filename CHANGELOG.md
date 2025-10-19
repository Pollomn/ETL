# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [1.0.0] - 2025-01-18

### Ajouté
- **Pipeline ETL complet** pour site de dropshipping vêtements
- **Génération de données** : Scripts pour créer clients, produits, commandes réalistes
- **Infrastructure Kafka** : Redpanda (Kafka-compatible) avec Docker Compose
- **Producer Kafka** : Deux modes (replay CSV, stream continu) avec rate limiting
- **Consumer Snowflake** : Ingestion automatique des événements vers raw.orders_events
- **Infrastructure Snowflake** : Warehouse, database, schémas (RAW, STAGING, PROD)
- **ETL automatisé** : Streams et Tasks Snowflake pour ingestion automatique
- **Validation qualité** : Scripts de vérification avec rapports JSON
- **Dashboard Streamlit** : Monitoring temps réel avec KPIs et visualisations
- **Documentation complète** : README, checklist captures, guides d'utilisation
- **Makefile** : Commandes automatisées pour setup et exécution
- **Configuration** : Variables d'environnement, .env.example, .gitignore

### Fonctionnalités techniques
- **Génération données** : 1000 clients, 200 produits, 5000 commandes par défaut
- **Streaming** : Rate limiting configurable, gestion graceful shutdown
- **Snowflake** : Schémas typés, contraintes FK, index de performance
- **Monitoring** : KPIs temps réel, top produits, tendances quotidiennes
- **Validation** : Checks automatiques (doublons, qualité, cohérence)
- **Reproductibilité** : Seeds fixes, configuration versionnée

### Architecture
```
Data Generator → CSV → Kafka Producer → Redpanda → Consumer → Snowflake RAW → Stream → Task → PROD → Streamlit
```

### Scripts créés
- `scripts/export_seed.py` : Génération et export CSV
- `scripts/producer.py` : Producer Kafka (replay/stream)
- `scripts/consumer_snowflake.py` : Consumer → Snowflake
- `scripts/validate.py` : Validation qualité + rapport JSON
- `streamlit_monitor/app.py` : Dashboard monitoring

### Infrastructure SQL
- `snowflake/01_create_warehouse_db_schemas.sql` : Warehouse, DB, schémas
- `snowflake/02_create_tables.sql` : Tables production
- `snowflake/03_create_stream_and_task.sql` : Stream + Task automatisée
- `snowflake/04_validate_ingestion.sql` : Requêtes de validation
- `snowflake/run_all.sh` : Exécution séquentielle

### Documentation
- `README.md` : Guide complet d'utilisation
- `docs/CAPTURE_CHECKLIST.md` : Instructions captures/vidéo
- `.env.example` : Template configuration
- `LICENSE` : MIT License

### Dépendances ajoutées
- `kafka-python-ng` : Client Kafka
- `streamlit` : Dashboard web
- `plotly` : Visualisations interactives
- `pyarrow` : Optimisation pandas
- `python-dotenv` : Gestion variables d'environnement

### Commandes Makefile
- `make install` : Installation dépendances
- `make generate-data` : Génération données seed
- `make docker-up/down` : Gestion Redpanda
- `make validate` : Validation qualité
- `make monitor` : Dashboard Streamlit
- `make all` : Setup complet

### Choix techniques
- **Échelle** : 1000 clients, 200 produits, 5000 commandes (réaliste sans surcharge)
- **Producer** : Deux modes (replay reproductible, stream continu)
- **Credentials** : Variables d'environnement sécurisées
- **Dépendances** : pyproject.toml + requirements.txt (compatibilité)
- **Task Snowflake** : Cron 1 minute (équilibre latence/coût)
- **Stream** : Capture CDC automatique
- **Streamlit** : Simplicité et rapidité de déploiement

### Tests et validation
- Scripts idempotents (relançables sans erreur)
- Validation automatique des données
- Gestion d'erreurs robuste
- Logs détaillés pour debugging
- Rapports JSON pour traçabilité

### Prochaines étapes
1. Exécution locale : `make all`
2. Configuration Snowflake : `bash snowflake/run_all.sh`
3. Test pipeline : Producer + Consumer
4. Génération captures/vidéo
5. Livraison finale
