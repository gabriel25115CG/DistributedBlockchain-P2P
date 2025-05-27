import threading
import sys
import time

from node.blockchain import Blockchain
from node.network import P2PNode
from node.wallet import Wallet
from node.api import app, setup_api

def run_flask(port):
    app.run(port=port + 1000, debug=False, use_reloader=False)

def print_menu():
    print("""
--- UTBM Blockchain Node CLI ---
1. Voir la blockchain
2. Voir les peers connectés
3. Consulter le solde d'une adresse
4. Créer une transaction
5. Miner un bloc
6. Quitter
""")

def cli_loop(blockchain, network, wallet):
    while True:
        print_menu()
        choice = input("Choix: ").strip()

        if choice == '1':
            chain = blockchain.chain
            print(f"Chaîne (hauteur {len(chain)}):")
            for block in chain:
                print(f" - Bloc {block['index']}, nonce={block['nonce']}, txs={len(block['transactions'])}")

        elif choice == '2':
            peers = network.get_peers()
            print(f"Peers connectés ({len(peers)}): {peers}")

        elif choice == '3':
            addr = input("Adresse: ").strip()
            balance = wallet.get_balance(blockchain, addr)
            print(f"Solde de {addr} : {balance} UTBM")

        elif choice == '4':
            sender = input("Sender: ").strip()
            recipient = input("Recipient: ").strip()
            try:
                amount = float(input("Amount: ").strip())
            except ValueError:
                print("Montant invalide")
                continue

            tx = {
                "sender": sender,
                "recipient": recipient,
                "amount": amount
            }
            blockchain.add_new_transaction(tx)
            print("Transaction ajoutée (en attente)")

        elif choice == '5':
            miner_address = input("Adresse du mineur: ").strip()
            block = blockchain.mine(miner_address)
            if block:
                print(f"Bloc miné avec succès : index {block['index']}")
            else:
                print("Aucune transaction à miner")

        elif choice == '6':
            print("Au revoir !")
            break

        else:
            print("Choix invalide")

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m node.node <port>")
        return

    port = int(sys.argv[1])

    # Instancie blockchain, network et wallet
    blockchain = Blockchain()
    network = P2PNode(port)
    wallet = Wallet()

    # Démarre le P2P network (écoute des connexions)
    network.start()

    # Liste des peers connus - adapte cette liste selon ta configuration réseau
    known_peers = [5001, 5002, 5003]

    # Connexion aux autres peers connus (sauf soi-même)
    for peer_port in known_peers:
        if peer_port != port:
            try:
                network.connect_to_peer(peer_port)
                time.sleep(0.1)  # Petit délai pour éviter surcharge réseau au démarrage
            except Exception as e:
                print(f"Erreur en se connectant au peer {peer_port}: {e}")

    # Injecte dans l'API Flask
    setup_api(blockchain, network, wallet)

    # Lance Flask dans un thread daemon
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()

    print(f"Node démarré sur le port {port} (API sur {port + 1000})")

    # Attend quelques secondes pour que le réseau démarre bien
    time.sleep(1)

    # Lance la boucle CLI dans le thread principal
    cli_loop(blockchain, network, wallet)

if __name__ == "__main__":
    main()
