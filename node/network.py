import socket
import threading
import json
from config import PEER_TIMEOUT

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

    def start(self):
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Erreur lors de l'acceptation d'une connexion : {e}")

    def handle_peer(self, conn):
        try:
            data = conn.recv(4096)
            if not data:
                return
            message = json.loads(data.decode())
            msg_type = message.get('type')

            if msg_type == 'NEW_PEER':
                peer_port = message.get('port')
                if peer_port and peer_port != self.port:
                    with self.lock:
                        self.peers.add(peer_port)

                    # Prépare et envoie la liste des peers connus
                    with self.lock:
                        peers_list = list(self.peers)
                    conn.send(json.dumps({'type': 'PEERS', 'peers': peers_list}).encode())

                    # Tente de se connecter à tous les autres peers pour propager la connaissance
                    for p in peers_list:
                        if p != self.port and p != peer_port:
                            self.connect_to_peer(p)

            elif msg_type == 'GET_PEERS':
                with self.lock:
                    peers_list = list(self.peers)
                conn.send(json.dumps({'type': 'PEERS', 'peers': peers_list}).encode())

            else:
                conn.send(json.dumps({'error': 'Type de message inconnu'}).encode())

        except Exception as e:
            print(f"Erreur gestion peer: {e}")
        finally:
            conn.close()

    def connect_to_peer(self, peer_port):
        if peer_port == self.port:
            return  # Ne pas se connecter à soi-même
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
                    # Filtrer les ports invalides ou soi-même
                    filtered_peers = [p for p in response['peers'] if p != self.port]
                    self.peers.update(filtered_peers)
            s.close()
        except Exception as e:
            print(f"Erreur connexion peer {peer_port}: {e}")

    def get_peers(self):
        with self.lock:
            return list(self.peers)

    def stop(self):
        self.running = False
        try:
            self.server.close()
        except Exception:
            pass
