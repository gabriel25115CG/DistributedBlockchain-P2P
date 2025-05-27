import threading
import sys
import time
from colorama import init, Fore, Style

from node.blockchain import Blockchain
from node.network import P2PNode
from node.wallet import Wallet
from node.api import app, setup_api

# Initialisation de colorama pour colorer le terminal (compatible Windows)
init(autoreset=True)

def run_flask(port):
    app.run(port=port + 1000, debug=False, use_reloader=False)

def print_menu():
    print(Fore.BLUE + "\n--- UTBM Blockchain Node CLI ---" + Style.RESET_ALL)
    print(Fore.CYAN + "1." + Style.RESET_ALL + " Voir la blockchain")
    print(Fore.CYAN + "2." + Style.RESET_ALL + " Voir les peers connectés")
    print(Fore.CYAN + "3." + Style.RESET_ALL + " Consulter le solde d'une adresse")
    print(Fore.CYAN + "4." + Style.RESET_ALL + " Créer une transaction")
    print(Fore.CYAN + "5." + Style.RESET_ALL + " Miner un bloc")
    print(Fore.CYAN + "6." + Style.RESET_ALL + " Voir mon portefeuille")
    print(Fore.CYAN + "7." + Style.RESET_ALL + " Quitter\n")

def print_blockchain(blockchain):
    chain = blockchain.chain
    print(Fore.MAGENTA + f"\nChaîne (hauteur {len(chain)}):" + Style.RESET_ALL)
    for block in chain:
        print(Fore.YELLOW + f" - Bloc {block.index}, nonce={block.nonce}, txs={len(block.transactions)}" + Style.RESET_ALL)
        if block.transactions:
            print(Fore.CYAN + "   Transactions :" + Style.RESET_ALL)
            for i, tx in enumerate(block.transactions, 1):
                sender = tx['sender']
                recipient = tx['recipient']
                amount = tx['amount']
                print(
                    f"    {Fore.GREEN}{i}.{Style.RESET_ALL} "
                    f"De {Fore.RED}{sender}{Style.RESET_ALL} à {Fore.BLUE}{recipient}{Style.RESET_ALL} : "
                    f"{Fore.YELLOW}{amount} UTBM{Style.RESET_ALL}"
                )
        else:
            print(Fore.RED + "   Pas de transactions." + Style.RESET_ALL)
        print()  # Ligne vide entre les blocs

def cli_loop(blockchain, network, wallet):
    while True:
        print_menu()
        choice = input(Fore.YELLOW + "Choix: " + Style.RESET_ALL).strip()

        if choice == '1':
            print_blockchain(blockchain)

        elif choice == '2':
            peers = network.get_peers()
            print(Fore.MAGENTA + f"\nPeers connectés ({len(peers)}): " + Style.RESET_ALL + f"{peers}\n")

        elif choice == '3':
            addr = input(Fore.YELLOW + "Adresse: " + Style.RESET_ALL).strip()
            balance = wallet.get_balance(blockchain, addr)
            print(Fore.GREEN + f"Solde de {addr} : {balance} UTBM\n")

        elif choice == '4':
            sender = input(Fore.YELLOW + "Sender: " + Style.RESET_ALL).strip()
            recipient = input(Fore.YELLOW + "Recipient: " + Style.RESET_ALL).strip()
            try:
                amount = float(input(Fore.YELLOW + "Amount: " + Style.RESET_ALL).strip())
            except ValueError:
                print(Fore.RED + "Montant invalide\n" + Style.RESET_ALL)
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
                        print(Fore.RED + f"Erreur en envoyant la transaction au peer {peer}: {e}" + Style.RESET_ALL)

                print(Fore.GREEN + "Transaction ajoutée (en attente) et propagée aux peers\n" + Style.RESET_ALL)
            else:
                print(Fore.RED + "Transaction refusée (solde insuffisant)\n" + Style.RESET_ALL)

        elif choice == '5':
            miner_address = input(Fore.YELLOW + f"Adresse du mineur [{wallet.get_address()}]: " + Style.RESET_ALL).strip()
            if miner_address == '':
                miner_address = wallet.get_address()
            block = blockchain.mine(miner_address)
            if block:
                print(Fore.GREEN + f"Bloc miné avec succès : index {block.index}\n" + Style.RESET_ALL)
                peers = network.get_peers()
                for peer in peers:
                    try:
                        network.send_block(peer, block)
                    except Exception as e:
                        print(Fore.RED + f"Erreur en envoyant le bloc au peer {peer}: {e}" + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + "Aucune transaction à miner\n" + Style.RESET_ALL)

        elif choice == '6':
            address = wallet.get_address()
            balance = wallet.get_balance(blockchain, address)
            print(Fore.GREEN + f"Votre portefeuille ({address}) contient : {balance} UTBM\n" + Style.RESET_ALL)

        elif choice == '7':
            print(Fore.CYAN + "Au revoir !" + Style.RESET_ALL)
            network.stop()
            break

        else:
            print(Fore.RED + "Choix invalide\n" + Style.RESET_ALL)

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
                        print(Fore.GREEN + f"Synchronisation : chaîne mise à jour depuis le peer {peer}\n" + Style.RESET_ALL)
                        return True
        except Exception as e:
            print(Fore.RED + f"Erreur lors de la synchronisation avec le peer {peer}: {e}" + Style.RESET_ALL)
    print(Fore.YELLOW + "Synchronisation impossible ou chaîne locale à jour\n" + Style.RESET_ALL)
    return False

def validate_chain(chain):
    from node.blockchain import DIFFICULTY
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i - 1]
        if current.previous_hash != previous.hash:
            print(Fore.RED + f"Chaîne invalide à l'index {i} : previous_hash incorrect" + Style.RESET_ALL)
            return False
        if not current.hash.startswith('0' * DIFFICULTY) or current.hash != current.compute_hash():
            print(Fore.RED + f"Chaîne invalide à l'index {i} : preuve de travail invalide" + Style.RESET_ALL)
            return False
    return True

def main():
    if len(sys.argv) < 2:
        print(Fore.RED + "Usage: python -m node.node <port>" + Style.RESET_ALL)
        return

    port = int(sys.argv[1])

    blockchain = Blockchain()
    network = P2PNode(port)
    wallet = Wallet()

    def on_receive_transaction(tx):
        if tx not in blockchain.unconfirmed_transactions:
            blockchain.add_new_transaction(tx)
            print(Fore.GREEN + f"\nNouvelle transaction reçue via le réseau: {tx}\n" + Style.RESET_ALL)

    def on_receive_block(block_data):
        success = blockchain.add_block_from_network(block_data)
        if success:
            print(Fore.GREEN + f"\nNouveau bloc ajouté via le réseau : index {block_data['index']}\n" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"\nBloc rejeté du réseau : index {block_data['index']}\n" + Style.RESET_ALL)

    network.set_transaction_callback(on_receive_transaction)
    network.set_block_callback(on_receive_block)

    print(Fore.BLUE + "\n=== Adresse unique de ce noeud (wallet) ===" + Style.RESET_ALL)
    print(wallet.get_address())
    print(Fore.BLUE + "==========================================\n" + Style.RESET_ALL)

    network.start()

    # Connexion aux peers connus
    known_peers = [5001, 5002, 5003]
    for peer_port in known_peers:
        if peer_port != port:
            try:
                network.connect_to_peer(peer_port)
                time.sleep(0.1)
            except Exception as e:
                print(Fore.RED + f"Erreur en se connectant au peer {peer_port}: {e}" + Style.RESET_ALL)

    # Synchroniser la blockchain
    synchronize_chain(blockchain, network)

    # Lancer l'API Flask
    setup_api(blockchain, network, wallet)
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()

    print(Fore.GREEN + f"Node démarré sur le port {port} (API sur {port + 1000})\n" + Style.RESET_ALL)
    time.sleep(1)

    cli_loop(blockchain, network, wallet)

if __name__ == "__main__":
    main()
