import threading
import sys
import time
from colorama import init, Fore, Style

from node.blockchain import Blockchain
from node.network import P2PNode
from node.wallet import Wallet
from node.api import app, setup_api

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

def cli_loop(blockchain, network, wallet):
    while True:
        print_menu()
        choice = input(Fore.YELLOW + "Choix: " + Style.RESET_ALL).strip()

        if choice == '1':
            blockchain.print_chain()

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

            tx = {"sender": sender, "recipient": recipient, "amount": amount}
            if blockchain.add_new_transaction(tx):
                for peer in network.get_peers():
                    try:
                        network.send_transaction(peer, tx)
                    except Exception as e:
                        print(Fore.RED + f"Erreur en envoyant la transaction au peer {peer}: {e}" + Style.RESET_ALL)
                print(Fore.GREEN + "Transaction ajoutée et propagée\n" + Style.RESET_ALL)
            else:
                print(Fore.RED + "Transaction refusée (solde insuffisant)\n" + Style.RESET_ALL)

        elif choice == '5':
            miner_address = input(Fore.YELLOW + f"Adresse du mineur [{wallet.get_address()}]: " + Style.RESET_ALL).strip()
            if miner_address == '':
                miner_address = wallet.get_address()

            block = blockchain.mine(miner_address)
            if block:
                print(Fore.GREEN + f"Bloc miné avec succès : index {block.index}\n" + Style.RESET_ALL)
                for peer in network.get_peers():
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
    """Essaye de synchroniser la blockchain depuis les pairs."""
    from node.block import Block

    for peer in network.get_peers():
        try:
            chain_data = network.request_chain(peer)
            if chain_data and len(chain_data) > len(blockchain.chain):
                new_chain = [Block.from_dict(b) for b in chain_data]
                if validate_chain(new_chain):
                    blockchain.chain = new_chain
                    blockchain.unconfirmed_transactions = []
                    print(Fore.GREEN + f"Chaîne synchronisée depuis le peer {peer}\n" + Style.RESET_ALL)
                    return True
        except Exception as e:
            print(Fore.RED + f"Erreur de synchronisation avec le peer {peer}: {e}" + Style.RESET_ALL)

    print(Fore.YELLOW + "Chaîne locale à jour ou synchronisation impossible\n" + Style.RESET_ALL)
    return False

def validate_chain(chain):
    """Valide l'intégrité d'une chaîne de blocs."""
    from node.blockchain import DIFFICULTY
    for i in range(1, len(chain)):
        current, previous = chain[i], chain[i - 1]
        if current.previous_hash != previous.hash:
            print(Fore.RED + f"Chaîne invalide à l'index {i} : mauvais previous_hash" + Style.RESET_ALL)
            return False
        if not current.hash.startswith('0' * DIFFICULTY) or current.hash != current.compute_hash():
            print(Fore.RED + f"Chaîne invalide à l'index {i} : preuve de travail invalide" + Style.RESET_ALL)
            return False
    return True

def periodic_sync(blockchain, network, interval=30):
    """Synchronisation périodique avec les peers."""
    while True:
        time.sleep(interval)
        if synchronize_chain(blockchain, network):
            print(Fore.GREEN + "Synchronisation périodique effectuée\n" + Style.RESET_ALL)

def main():
    if len(sys.argv) < 2:
        print(Fore.RED + "Usage: python -m node.node <port>" + Style.RESET_ALL)
        return

    port = int(sys.argv[1])

    blockchain = Blockchain()
    network = P2PNode(port)
    wallet = Wallet()
    network.set_blockchain(blockchain)

    def on_receive_transaction(tx):
        if tx not in blockchain.unconfirmed_transactions:
            blockchain.add_new_transaction(tx)
            print(Fore.GREEN + f"\nTransaction reçue : {tx}\n" + Style.RESET_ALL)

    def on_receive_block(block_data):
        success = blockchain.add_block_from_network(block_data)
        if success:
            print(Fore.GREEN + f"\nBloc ajouté via réseau : index {block_data['index']}\n" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"\nBloc rejeté : tentative de resynchro...\n" + Style.RESET_ALL)
            synchronize_chain(blockchain, network)

    network.set_transaction_callback(on_receive_transaction)
    network.set_block_callback(on_receive_block)

    print(Fore.BLUE + "\n=== Adresse de ce noeud ===" + Style.RESET_ALL)
    print(wallet.get_address())
    print(Fore.BLUE + "===========================\n" + Style.RESET_ALL)

    network.start()

    # Connexion aux peers connus
    for peer_port in [5001, 5002, 5003]:
        if peer_port != port:
            try:
                network.connect_to_peer(peer_port)
                time.sleep(0.1)
            except Exception as e:
                print(Fore.RED + f"Erreur de connexion au peer {peer_port}: {e}" + Style.RESET_ALL)

    # Synchronisation initiale
    synchronize_chain(blockchain, network)

    # Lancer les threads : sync périodique et API Flask
    threading.Thread(target=periodic_sync, args=(blockchain, network), daemon=True).start()
    setup_api(blockchain, network, wallet)
    threading.Thread(target=run_flask, args=(port,), daemon=True).start()

    print(Fore.GREEN + f"Node lancé sur le port {port} (API sur {port + 1000})\n" + Style.RESET_ALL)

    cli_loop(blockchain, network, wallet)

if __name__ == "__main__":
    main()
