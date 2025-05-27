import sys
import time
import threading
from node.network import P2PNode
from node.blockchain import Blockchain
from node.wallet import Wallet
from node.api import app, blockchain, network, wallet
from config import PORT_BASE

class Node:
    def __init__(self, port):
        self.port = port
        self.blockchain = Blockchain()
        self.network = P2PNode(port)
        self.wallet = Wallet()
        # Injection dans api
        global blockchain, network, wallet
        blockchain = self.blockchain
        network = self.network
        wallet = self.wallet

    def start(self):
        print(f"Démarrage nœud sur port {self.port}")
        self.network.start()
        # Connexion aux peers initiaux (par exemple port_base + 1, +2 ...)
        for p in range(PORT_BASE, PORT_BASE + 5):
            if p != self.port:
                self.network.connect_to_peer(p)

        # Start Flask API
        threading.Thread(target=lambda: app.run(port=self.port+1000, debug=False, use_reloader=False)).start()

        while True:
            time.sleep(10)
            print(f"Peers connectés: {self.network.get_peers()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    node = Node(port)
    node.start()
