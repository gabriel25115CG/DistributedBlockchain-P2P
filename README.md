# UTBM Blockchain Node

---

## 1. Présentation

**UTBM Blockchain Node** est un prototype simple d’implémentation d’une blockchain, permettant à plusieurs nœuds (nodes) de se connecter en réseau peer-to-peer, de gérer des transactions, miner des blocs, et synchroniser la chaîne.

Chaque nœud possède :
- Une blockchain locale
- Un portefeuille (wallet) unique
- Une API REST (via Flask) pour interagir avec la blockchain
- Une interface CLI (ligne de commande) pour gérer la blockchain manuellement

---

## 2. Fonctionnalités principales

- Gestion d’une blockchain avec preuve de travail (Proof of Work)
- Création et validation de transactions
- Minage de blocs
- Réseau P2P pour synchroniser la blockchain et propager transactions/blocs
- Portefeuille avec adresse unique et consultation du solde
- API REST pour accès distant
- CLI intuitive pour interaction en temps réel

---

## 3. Structure du projet

```
project/
├── node/
│   ├── __init__.py
│   ├── blockchain.py      # Classe Blockchain et logique de validation
│   ├── block.py           # Classe Block (bloc unique)
│   ├── wallet.py          # Gestion du portefeuille et des clés
│   ├── network.py         # Réseau P2P (connexion, échanges)
│   ├── api.py             # API Flask pour interaction HTTP
│   └── node.py            # Point d’entrée principal, CLI + lancement réseau et API
├── requirements.txt       # Dépendances Python
└── README.md              # Cette documentation
```

---

## 4. Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/gabriel25115CG/DistributedBlockchain-P2P.git
   cd DistributedBlockchain-P2P.git
   ```

2. Installer les dépendances Python :
   ```bash
   pip install -r requirements.txt
   ```

   **Dépendances clés :**
   - Flask (API)
   - Colorama (couleurs terminal)
   - Autres dépendances standards Python 3.7+

---

## 5. Utilisation

### Lancer un nœud

```bash
python -m node.node <port>
```

Exemple :
```bash
python -m node.node 5001
```

- Le nœud démarre une API Flask sur `<port + 1000>` (ex. 6001)
- L’interface CLI s’active pour gérer la blockchain localement

---

### Options du CLI

| Choix | Action                                  |
|-------|----------------------------------------|
| 1     | Afficher la blockchain                  |
| 2     | Voir les peers connectés                |
| 3     | Consulter le solde d’une adresse        |
| 4     | Créer une transaction                   |
| 5     | Miner un bloc                           |
| 6     | Voir son portefeuille                   |
| 7     | Quitter le nœud                        |

---

### Exemple de création d’une transaction

- Choisir `4` dans le menu CLI
- Entrer l’adresse expéditrice (`sender`)
- Entrer l’adresse destinataire (`recipient`)
- Entrer le montant à transférer

---

### Minage

- Choisir `5` dans le menu CLI
- Indiquer l’adresse du mineur (par défaut ton wallet)
- Le nœud mine un bloc avec les transactions en attente

---

## 6. Synchronisation

Lors du démarrage, le nœud tente de synchroniser sa blockchain avec les peers connus (ports 5001, 5002, 5003 par défaut).

---

## 7. Architecture technique

### Blockchain

- Liste de blocs, chaque bloc contenant :
  - Index
  - Timestamp
  - Liste de transactions
  - Nonce (preuve de travail)
  - Hash du bloc précédent
  - Hash du bloc courant

- Validation de la chaîne : contrôle de la continuité des hashes et difficulté (ex : nombre de zéros en tête)

### Réseau P2P

- Connexion à peers via sockets
- Propagation des transactions et blocs
- Callbacks pour réception de données réseau

### API Flask

- Expose des endpoints pour consulter la blockchain, créer des transactions, miner, etc.
- Écoute sur `port + 1000`

---

## 8. Développement et contribution

- Forker le dépôt
- Créer une branche pour vos modifications
- Tester rigoureusement (notamment les fonctions de synchronisation)
- Soumettre une pull request détaillée

---

## 9. Limitations et améliorations possibles

- Pas encore de mécanisme robuste de consensus (ex: Proof of Stake)
- Pas d’interface graphique Web
- Gestion simplifiée des erreurs réseau
- Optimisation de la propagation des transactions et blocs
- Sécurité cryptographique à renforcer (gestion des clés privées)
