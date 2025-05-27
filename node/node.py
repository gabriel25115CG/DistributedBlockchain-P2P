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
6. Voir mon portefeuille
7. Quitter
""")

def cli_loop(blockchain, network, wallet):
    while True:
        print_menu()
        choice = input("Choix: ").strip()

        if choice == '1':
            chain = blockchain.chain
            print(f"Chaîne (hauteur {len(chain)}):")
            for block in chain:
                print(f" - Bloc {block.index}, nonce={block.nonce}, txs={len(block.transactions)}")

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
            if blockchain.add_new_transaction(tx):
                peers = network.get_peers()
                for peer in peers:
                    try:
                        network.send_transaction(peer, tx)
                    except Exception as e:
                        print(f"Erreur en envoyant la transaction au peer {peer}: {e}")

                print("Transaction ajoutée (en attente) et propagée aux peers")
            else:
                print("Transaction refusée (solde insuffisant)")

        elif choice == '5':
            miner_address = input(f"Adresse du mineur [{wallet.get_address()}]: ").strip()
            if miner_address == '':
                miner_address = wallet.get_address()
            block = blockchain.mine(miner_address)
            if block:
                print(f"Bloc miné avec succès : index {block.index}")
                peers = network.get_peers()
                for peer in peers:
                    try:
                        network.send_block(peer, block)
                    except Exception as e:
                        print(f"Erreur en envoyant le bloc au peer {peer}: {e}")
            else:
                print("Aucune transaction à miner")

        elif choice == '6':
            address = wallet.get_address()
            balance = wallet.get_balance(blockchain, address)
            print(f"Votre portefeuille ({address}) contient : {balance} UTBM")

        elif choice == '7':
            print("Au revoir !")
            network.stop()
            break

        else:
            print("Choix invalide")

def synchronize_chain(blockchain, network):
    from node.block import Block

    peers = network.get_peers()
    for peer in peers:
        try:
            chain_data = network.request_chain(peer)
            if chain_data:
                if len(chain_data) > len(blockchain.chain):
                    new_chain = [Block.from_dict(b) for b in chain_data]
                    if validate_chain(new_chain):
                        blockchain.chain = new_chain
                        blockchain.unconfirmed_transactions = []
                        print(f"Synchronisation : chaîne mise à jour depuis le peer {peer}")
                        return True
        except Exception as e:
            print(f"Erreur lors de la synchronisation avec le peer {peer}: {e}")
    print("Synchronisation impossible ou chaîne locale à jour")
    return False

def validate_chain(chain):
    from node.blockchain import DIFFICULTY
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i - 1]
        if current.previous_hash != previous.hash:
            print(f"Chaîne invalide à l'index {i} : previous_hash incorrect")
            return False
        if not current.hash.startswith('0' * DIFFICULTY) or current.hash != current.compute_hash():
            print(f"Chaîne invalide à l'index {i} : preuve de travail invalide")
            return False
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m node.node <port>")
        return

    port = int(sys.argv[1])

    blockchain = Blockchain()
    network = P2PNode(port)
    wallet = Wallet()

    def on_receive_transaction(tx):
        if tx not in blockchain.unconfirmed_transactions:
            blockchain.add_new_transaction(tx)
            print(f"\nNouvelle transaction reçue via le réseau: {tx}\n")

    def on_receive_block(block_data):
        success = blockchain.add_block_from_network(block_data)
        if success:
            print(f"\nNouveau bloc ajouté via le réseau : index {block_data['index']}\n")
        else:
            print(f"\nBloc rejeté du réseau : index {block_data['index']}\n")

    network.set_transaction_callback(on_receive_transaction)
    network.set_block_callback(on_receive_block)

    print("\n=== Adresse unique de ce noeud (wallet) ===")
    print(wallet.get_address())
    print("==========================================\n")

    network.start()

    # Connexion aux peers
    known_peers = [5001, 5002, 5003]
    for peer_port in known_peers:
        if peer_port != port:
            try:
                network.connect_to_peer(peer_port)
                time.sleep(0.1)
            except Exception as e:
                print(f"Erreur en se connectant au peer {peer_port}: {e}")

    # Synchroniser la blockchain
    synchronize_chain(blockchain, network)

    # Lancer l'API
    setup_api(blockchain, network, wallet)
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()

    print(f"Node démarré sur le port {port} (API sur {port + 1000})")
    time.sleep(1)

    cli_loop(blockchain, network, wallet)

if __name__ == "__main__":
    main()
