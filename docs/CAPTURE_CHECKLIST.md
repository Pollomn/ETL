# 📸 Checklist pour Captures et Vidéo

Ce document fournit les instructions détaillées pour générer les preuves de fonctionnement du pipeline.

## 🎯 Objectifs des captures

1. **Snowsight** : Montrer les données dans Snowflake (raw vs prod)
2. **Vidéo** : Démonstration complète du pipeline en action
3. **Dashboard** : Interface Streamlit fonctionnelle

## 📋 Checklist de préparation

### Avant de commencer

- [ ] Pipeline complètement configuré et testé
- [ ] Données générées (`make generate-data`)
- [ ] Snowflake configuré (`bash snowflake/run_all.sh`)
- [ ] Redpanda démarré (`make docker-up`)
- [ ] Tous les scripts fonctionnels

### Vérifications préalables

```bash
# 1. Vérifier que les données sont générées
ls -la data/seed/
# Doit contenir: customers.csv, inventory.csv, orders.csv

# 2. Vérifier que Redpanda fonctionne
docker ps
# Doit voir le conteneur redpanda

# 3. Vérifier la connexion Snowflake
snowsql -a $SNOW_ACCOUNT -u $SNOW_USER -q "SELECT 1;"
```

## 📸 Captures Snowsight

### Capture 1 : Données RAW

1. Ouvrir Snowsight
2. Exécuter la requête :
   ```sql
   SELECT COUNT(*) as raw_events_count FROM raw.orders_events;
   ```
3. Capturer l'écran montrant le résultat

### Capture 2 : Données PROD

1. Dans Snowsight, exécuter :
   ```sql
   SELECT COUNT(*) as prod_orders_count FROM prod.orders;
   ```
2. Capturer l'écran montrant le résultat

### Capture 3 : Comparaison

1. Exécuter la requête de validation :
   ```sql
   SELECT 
       'Raw Events' as table_name,
       COUNT(*) as record_count
   FROM raw.orders_events
   UNION ALL
   SELECT 
       'Production Orders' as table_name,
       COUNT(*) as record_count
   FROM prod.orders;
   ```
2. Capturer l'écran avec les deux compteurs

## 🎥 Enregistrement vidéo (60 secondes)

### Timeline recommandée

**0-10s : Démarrage du producer**
- Ouvrir terminal
- Lancer : `python scripts/producer.py --mode replay --rate 10`
- Montrer les logs de démarrage

**10-20s : Consumer en action**
- Ouvrir second terminal
- Lancer : `python scripts/consumer_snowflake.py`
- Montrer les logs d'insertion

**20-35s : Snowsight en temps réel**
- Ouvrir Snowsight
- Exécuter : `SELECT COUNT(*) FROM raw.orders_events;`
- Rafraîchir plusieurs fois pour montrer l'augmentation
- Exécuter : `SELECT COUNT(*) FROM prod.orders;`

**35-50s : Task Snowflake**
- Dans Snowsight, exécuter :
  ```sql
  ALTER TASK prod.ingest_orders_task EXECUTE;
  ```
- Attendre quelques secondes
- Vérifier que prod.orders s'incrémente

**50-60s : Dashboard Streamlit**
- Ouvrir : `streamlit run streamlit_monitor/app.py`
- Montrer les KPIs et graphiques

### Commandes d'enregistrement

#### Option 1 : macOS (QuickTime + ffmpeg)

```bash
# Enregistrement écran avec QuickTime
# 1. Ouvrir QuickTime Player
# 2. Fichier > Nouvel enregistrement d'écran
# 3. Sélectionner la zone d'écran
# 4. Enregistrer pendant 60 secondes

# Conversion avec ffmpeg (optionnel)
ffmpeg -i screen_recording.mov -t 60 -c:v libx264 -crf 23 demo.mp4
```

#### Option 2 : OBS Studio (Cross-platform)

1. **Configuration OBS** :
   - Créer une scène "Pipeline Demo"
   - Ajouter source "Capture d'écran"
   - Résolution : 1920x1080

2. **Enregistrement** :
   - Bouton "Démarrer l'enregistrement"
   - Durée : 60 secondes
   - Format : MP4

3. **Post-traitement** :
   ```bash
   # Compression (optionnel)
   ffmpeg -i obs_recording.mp4 -c:v libx264 -crf 23 -preset fast demo.mp4
   ```

#### Option 3 : ffmpeg direct (macOS)

```bash
# Enregistrement direct avec ffmpeg
ffmpeg -f avfoundation -i "1:0" -t 60 -r 30 -c:v libx264 -crf 23 demo.mp4

# Explication des paramètres :
# -f avfoundation : Utilise AVFoundation (macOS)
# -i "1:0" : Écran 1, audio 0
# -t 60 : Durée 60 secondes
# -r 30 : 30 FPS
# -c:v libx264 : Codec vidéo
# -crf 23 : Qualité (18-28, plus bas = meilleure qualité)
```

## 🧪 Tests de validation

### Test 1 : Pipeline complet

```bash
# 1. Nettoyer l'environnement
make clean
make docker-down

# 2. Setup complet
make all

# 3. Configurer Snowflake
bash snowflake/run_all.sh

# 4. Test end-to-end
python scripts/producer.py --mode replay --rate 10 &
PRODUCER_PID=$!

python scripts/consumer_snowflake.py &
CONSUMER_PID=$!

# Attendre 30 secondes
sleep 30

# Arrêter les processus
kill $PRODUCER_PID $CONSUMER_PID

# 5. Validation
python scripts/validate.py

# 6. Dashboard
streamlit run streamlit_monitor/app.py
```

### Test 2 : Vérifications rapides

```bash
# Vérifier Kafka
docker exec -it redpanda rpk topic list
docker exec -it redpanda rpk topic consume orders_topic --num 5

# Vérifier Snowflake
snowsql -a $SNOW_ACCOUNT -u $SNOW_USER -q "SELECT COUNT(*) FROM raw.orders_events;"
snowsql -a $SNOW_ACCOUNT -u $SNOW_USER -q "SELECT COUNT(*) FROM prod.orders;"

# Vérifier les fichiers
ls -la data/seed/
ls -la reports/
```

## 📊 Métriques de succès

### Critères de validation

- [ ] **Données générées** : 1000 clients, 200 produits, 5000 commandes
- [ ] **Kafka fonctionnel** : Producer et consumer communiquent
- [ ] **Snowflake alimenté** : raw.orders_events contient des données
- [ ] **ETL automatisé** : prod.orders s'alimente via la task
- [ ] **Dashboard actif** : KPIs cohérents affichés
- [ ] **Validation passée** : Tous les checks de qualité OK

### Commandes de vérification

```bash
# 1. Compter les événements Kafka
docker exec -it redpanda rpk topic consume orders_topic --num 100 | wc -l

# 2. Compter les données Snowflake
snowsql -a $SNOW_ACCOUNT -u $SNOW_USER -q "
SELECT 
    (SELECT COUNT(*) FROM raw.orders_events) as raw_count,
    (SELECT COUNT(*) FROM prod.orders) as prod_count;"

# 3. Vérifier la task
snowsql -a $SNOW_ACCOUNT -u $SNOW_USER -q "
SELECT STATE, LAST_SCHEDULED_TIME, LAST_COMPLETED_TIME 
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) 
WHERE TASK_NAME = 'INGEST_ORDERS_TASK' 
ORDER BY SCHEDULED_TIME DESC LIMIT 1;"
```

## 🎬 Script de démonstration

### Script automatisé pour la vidéo

```bash
#!/bin/bash
# demo_script.sh - Script automatisé pour la démonstration

echo "🎬 Démarrage de la démonstration..."

# 1. Nettoyer et préparer
make clean
make docker-down
sleep 2

# 2. Setup
echo "📦 Setup de l'environnement..."
make all
sleep 5

# 3. Snowflake
echo "❄️ Configuration Snowflake..."
bash snowflake/run_all.sh
sleep 3

# 4. Démarrer le pipeline
echo "🚀 Démarrage du pipeline..."
python scripts/producer.py --mode replay --rate 10 &
PRODUCER_PID=$!

python scripts/consumer_snowflake.py &
CONSUMER_PID=$!

# 5. Attendre l'ingestion
echo "⏳ Attente de l'ingestion (30s)..."
sleep 30

# 6. Validation
echo "✅ Validation..."
python scripts/validate.py

# 7. Dashboard
echo "📊 Démarrage du dashboard..."
streamlit run streamlit_monitor/app.py &
DASHBOARD_PID=$!

# 8. Nettoyage après démo
echo "🧹 Nettoyage..."
sleep 10
kill $PRODUCER_PID $CONSUMER_PID $DASHBOARD_PID 2>/dev/null
make docker-down

echo "🎉 Démonstration terminée!"
```

## 📝 Notes finales

- **Durée vidéo** : 60 secondes maximum
- **Qualité** : 1080p minimum
- **Audio** : Optionnel, mais recommandé pour les explications
- **Format** : MP4 préféré
- **Taille** : < 100MB pour faciliter le partage

### Checklist finale

- [ ] Vidéo enregistrée (60s)
- [ ] Captures Snowsight
- [ ] Dashboard fonctionnel
- [ ] Validation passée
- [ ] Documentation complète
- [ ] Repo prêt pour livraison
