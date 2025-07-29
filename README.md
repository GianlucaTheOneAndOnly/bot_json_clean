Projet d'Automatisation iCare
Ce projet contient une collection de scripts et de modules pour automatiser des tâches et interagir avec l'API iCare. Grâce à sa structure de package, il est facile à installer et à utiliser.

Prérequis
Avant de commencer, assurez-vous d'avoir installé :

Python 3.8+

pip (généralement inclus avec Python)

⚙️ Installation
Pour faire fonctionner ce projet, vous devez l'installer en mode "éditable". Cette commande unique s'occupe de tout : elle installe les dépendances externes (comme pandas, requests, etc.) et rend votre propre code (api, utils...) accessible à Python.

Clonez ce dépôt sur votre machine locale :

Bash

git clone https://github.com/VOTRE_NOM_UTILISATEUR/VOTRE_PROJET.git
Naviguez dans le dossier du projet :

Bash

cd VOTRE_PROJET
Installez le projet et ses dépendances :

Bash

pip install -e .
Une fois ces étapes terminées, votre environnement est prêt.

▶️ Utilisation
Après l'installation, vous pouvez exécuter n'importe quel script directement depuis votre terminal. Par exemple, pour lancer un script situé dans src/bot/ :

Bash

python src/bot/task_temp_pusher.py
Toutes les importations, comme from api.client import ..., fonctionneront sans erreur.

📁 Structure du Projet
Le projet est organisé de la manière suivante pour garantir une séparation claire des responsabilités :

├── src/                # Contient tout le code source Python importable
│   ├── api/            # Module pour la communication avec l'API
│   ├── bot/            # Scripts principaux et logique métier
│   └── utils/          # Fonctions utilitaires
├── tests/              # Contient les tests pour le projet
├── config/             # Fichiers de configuration (.ini, etc.)
├── pyproject.toml      # Fichier de définition du projet et de ses dépendances
└── README.md           # Ce fichier