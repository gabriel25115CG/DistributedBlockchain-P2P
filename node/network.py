import socket
import threading
import json
from config import PEER_TIMEOUT

class P2PNode:
    def __init__(self, port):
        self.port = port
        self.peers = set()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', port))
        self.server.listen(5)
        self.running = True
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        while self.running:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()

    def handle_peer(self, conn):
        try:
            data = conn.recv(4096)
            message = json.loads(data.decode())
            if message['type'] == 'NEW_PEER':
                peer_port = message['port']
                with self.lock:
                    self.peers.add(peer_port)
                conn.send(json.dumps({'type': 'PEERS', 'peers': list(self.peers)}).encode())
            elif message['type'] == 'GET_PEERS':
                with self.lock:
                    conn.send(json.dumps({'type': 'PEERS', 'peers': list(self.peers)}).encode())
        except Exception as e:
            print(f"Erreur gestion peer: {e}")
        finally:
            conn.close()

    def connect_to_peer(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(PEER_TIMEOUT)
            s.connect(('127.0.0.1', port))
            message = json.dumps({'type': 'NEW_PEER', 'port': self.port})
            s.send(message.encode())
            data = s.recv(4096)
            response = json.loads(data.decode())
            if response['type'] == 'PEERS':
                with self.lock:
                    self.peers.update(response['peers'])
            s.close()
        except Exception as e:
            print(f"Erreur connexion peer {port}: {e}")

    def get_peers(self):
        with self.lock:
            return list(self.peers)

    def stop(self):
        self.running = False
        self.server.close()
