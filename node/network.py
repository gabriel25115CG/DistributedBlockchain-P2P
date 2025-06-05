import socket
import threading
import json
from config import PEER_TIMEOUT
from colorama import Fore, Style

class P2PNode:
    def __init__(self, port):
        self.port = port
        self.peers = set()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', port))
        self.server.listen(5)
        self.running = True
        self.lock = threading.Lock()
        self.transaction_callback = None
        self.block_callback = None
        self.blockchain = None  

    def set_blockchain(self, blockchain):  
        self.blockchain = blockchain

    def start(self):
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(Fore.RED + f"Erreur lors de l'acceptation d'une connexion : {e}" + Style.RESET_ALL)

    def handle_peer(self, conn):
        try:
            data = conn.recv(65536)
            if not data:
                return
            message = json.loads(data.decode())
            msg_type = message.get('type')

            if msg_type == 'NEW_PEER':
                peer_port = message.get('port')
                if peer_port and peer_port != self.port:
                    with self.lock:
                        self.peers.add(peer_port)
                    with self.lock:
                        peers_list = list(self.peers)
                    conn.send(json.dumps({'type': 'PEERS', 'peers': peers_list}).encode())
                    for p in peers_list:
                        if p != self.port and p != peer_port:
                            self.connect_to_peer(p)

            elif msg_type == 'GET_PEERS':
                with self.lock:
                    peers_list = list(self.peers)
                conn.send(json.dumps({'type': 'PEERS', 'peers': peers_list}).encode())

            elif msg_type == 'NEW_TRANSACTION':
                tx = message.get('transaction')
                if tx and self.transaction_callback:
                    self.transaction_callback(tx)
                conn.send(json.dumps({'type': 'ACK', 'message': 'Transaction reçue'}).encode())

            elif msg_type == 'NEW_BLOCK':
                block_data = message.get('block')
                if block_data and self.block_callback:
                    self.block_callback(block_data)
                conn.send(json.dumps({'type': 'ACK', 'message': 'Bloc reçu'}).encode())

            elif msg_type == 'GET_CHAIN':
                if self.blockchain:
                    chain_data = [block.to_dict() for block in self.blockchain.chain]
                    conn.send(json.dumps(chain_data).encode())
                else:
                    conn.send(json.dumps([]).encode())

            else:
                conn.send(json.dumps({'type': 'ERROR', 'message': 'Type de message inconnu'}).encode())

        except Exception as e:
            print(Fore.RED + f"Erreur dans handle_peer: {e}" + Style.RESET_ALL)
        finally:
            conn.close()

    def connect_to_peer(self, peer_port):
        if peer_port == self.port:
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(PEER_TIMEOUT)
            s.connect(('127.0.0.1', peer_port))
            message = json.dumps({'type': 'NEW_PEER', 'port': self.port})
            s.send(message.encode())
            data = s.recv(4096)
            response = json.loads(data.decode())
            if response.get('type') == 'PEERS':
                with self.lock:
                    filtered_peers = [p for p in response['peers'] if p != self.port]
                    self.peers.update(filtered_peers)
            s.close()
        except Exception as e:
            print(Fore.RED + f"Erreur connexion peer {peer_port}: {e}" + Style.RESET_ALL)

    def get_peers(self):
        with self.lock:
            return list(self.peers)

    def send_transaction(self, peer_port, transaction):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(PEER_TIMEOUT)
            s.connect(('127.0.0.1', peer_port))
            message = json.dumps({'type': 'NEW_TRANSACTION', 'transaction': transaction})
            s.send(message.encode())
            s.recv(1024)
            s.close()
        except Exception as e:
            print(Fore.RED + f"Erreur en envoyant la transaction au peer {peer_port}: {e}" + Style.RESET_ALL)

    def send_block(self, peer_port, block):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(PEER_TIMEOUT)
            s.connect(('127.0.0.1', peer_port))
            message = json.dumps({'type': 'NEW_BLOCK', 'block': block.to_dict()})
            s.send(message.encode())
            s.recv(1024)
            s.close()
        except Exception as e:
            print(Fore.RED + f"Erreur en envoyant le bloc au peer {peer_port}: {e}" + Style.RESET_ALL)

    def request_chain(self, peer_port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(PEER_TIMEOUT)
            s.connect(('127.0.0.1', peer_port))
            message = json.dumps({'type': 'GET_CHAIN'})
            s.send(message.encode())
            data = b''
            while True:
                part = s.recv(4096)
                if not part:
                    break
                data += part
            s.close()
            chain_data = json.loads(data.decode())
            return chain_data
        except Exception as e:
            print(Fore.RED + f"Erreur en récupérant la chaîne du peer {peer_port}: {e}" + Style.RESET_ALL)
            return None

    def stop(self):
        self.running = False
        self.server.close()

    def set_transaction_callback(self, callback):
        self.transaction_callback = callback

    def set_block_callback(self, callback):
        self.block_callback = callback
