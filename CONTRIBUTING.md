# 🤝 Guide de Contribution

## 🚀 **Comment contribuer au projet**

### **1. Fork et Clone**
```bash
# Fork le repository sur GitHub
# Puis cloner votre fork
git clone https://github.com/votre-username/dropshipping-data-pipeline.git
cd dropshipping-data-pipeline
```

### **2. Configuration de l'environnement**
```bash
# Installer les dépendances
pip install -r requirements.txt

# Copier la configuration
cp .env.example .env
# Éditer .env avec vos credentials
```

### **3. Créer une branche**
```bash
git checkout -b feature/nouvelle-fonctionnalite
```

### **4. Développement**
- Modifier le code
- Tester vos changements
- Documenter les modifications

### **5. Tests**
```bash
# Validation du pipeline
python scripts/validate.py

# Tests de connectivité
python -c "from kafka import KafkaConsumer; print('✅ Kafka OK')"
python -c "import snowflake.connector; print('✅ Snowflake OK')"
```

### **6. Commit et Push**
```bash
git add .
git commit -m "feat: description de votre modification"
git push origin feature/nouvelle-fonctionnalite
```

### **7. Pull Request**
- Créer une PR sur GitHub
- Décrire vos modifications
- Attendre la review

## 📋 **Standards de Code**

### **Python**
- Respecter PEP 8
- Documenter les fonctions
- Ajouter des tests si possible

### **SQL**
- Commenter les requêtes complexes
- Utiliser des noms explicites
- Tester sur un environnement de dev

### **Documentation**
- Mettre à jour README.md si nécessaire
- Documenter les nouvelles fonctionnalités
- Ajouter des exemples d'usage

## 🐛 **Rapport de Bugs**

### **Template de Bug Report**
```markdown
## 🐛 Description du Bug

### **Problème**
Description claire du problème

### **Reproduction**
1. Étapes pour reproduire
2. Comportement attendu
3. Comportement actuel

### **Environnement**
- OS: 
- Python version:
- Docker version:
- Snowflake account:

### **Logs**
```
Coller les logs d'erreur ici
```
```

## ✨ **Nouvelles Fonctionnalités**

### **Template de Feature Request**
```markdown
## ✨ Nouvelle Fonctionnalité

### **Description**
Description de la fonctionnalité souhaitée

### **Cas d'usage**
Pourquoi cette fonctionnalité est-elle utile ?

### **Implémentation suggérée**
Comment pensez-vous l'implémenter ?

### **Alternatives**
Autres solutions considérées
```

## 📚 **Ressources**

- [Documentation complète](docs/COMPLETE_DOCUMENTATION.md)
- [Guide des commandes](docs/COMMANDS_REFERENCE.md)
- [Documentation du code](docs/CODE_DOCUMENTATION.md)

## 🎯 **Roadmap**

- [ ] Support de multiples topics Kafka
- [ ] Dashboard avancé avec métriques temps réel
- [ ] Support de multiples environnements Snowflake
- [ ] Tests automatisés complets
- [ ] Déploiement cloud (AWS/Azure/GCP)

## 📞 **Contact**

Pour toute question, ouvrez une issue sur GitHub ou contactez l'équipe de développement.

---

**Merci de contribuer au projet ! 🚀**

