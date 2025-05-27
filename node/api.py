import threading
from flask import Flask, jsonify, request
from node.blockchain import Blockchain
from node.transaction import Transaction

app = Flask(__name__)

# Ces variables seront assignées depuis node.py via la fonction setup_api
blockchain = None
network = None
wallet = None

def setup_api(bc, net, wal):
    global blockchain, network, wallet
    blockchain = bc
    network = net
    wallet = wal

class NodeAPI:
    def __init__(self, blockchain, network, wallet):
        self.blockchain = blockchain
        self.network = network
        self.wallet = wallet

    def run(self, port):
        # Lance Flask dans un thread séparé
        self.port = port
        self.app_thread = threading.Thread(
            target=lambda: app.run(port=port, debug=False, use_reloader=False)
        )
        self.app_thread.daemon = True
        self.app_thread.start()

@app.route('/chain', methods=['GET'])
def get_chain():
    if blockchain is None:
        return jsonify({"error": "Blockchain non initialisée"}), 500

    chain_data = [block.to_dict() for block in blockchain.chain]
    return jsonify({"length": len(chain_data), "chain": chain_data})

@app.route('/mine', methods=['GET'])
def mine():
    if blockchain is None:
        return jsonify({"error": "Blockchain non initialisée"}), 500

    miner_address = request.args.get('miner_address')
    if not miner_address:
        return jsonify({"error": "Paramètre 'miner_address' manquant"}), 400

    block = blockchain.mine(miner_address)
    if not block:
        return jsonify({"message": "Pas de transactions à miner"}), 400
    return jsonify({"message": "Bloc miné", "block": block.to_dict()})

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    if blockchain is None:
        return jsonify({"error": "Blockchain non initialisée"}), 500

    tx_data = request.get_json()
    required_fields = ["sender", "recipient", "amount"]
    if not tx_data:
        return jsonify({"error": "Données transaction manquantes"}), 400

    for field in required_fields:
        if field not in tx_data:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

    try:
        amount = float(tx_data['amount'])
    except (ValueError, TypeError):
        return jsonify({"error": "Montant invalide"}), 400

    transaction = Transaction(tx_data['sender'], tx_data['recipient'], amount)
    blockchain.add_new_transaction(transaction.to_dict())
    return jsonify({"message": "Transaction ajoutée"}), 201

@app.route('/peers', methods=['GET'])
def peers():
    if network is None:
        return jsonify({"error": "Network non initialisé"}), 500
    peers = network.get_peers()
    return jsonify({"peers": peers})

@app.route('/balance/<string:address>', methods=['GET'])
def balance(address):
    if blockchain is None:
        return jsonify({"error": "Blockchain non initialisée"}), 500

    bal = 0
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx['recipient'] == address:
                bal += tx['amount']
            if tx['sender'] == address:
                bal -= tx['amount']
    return jsonify({"address": address, "balance": bal})
