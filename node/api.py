import threading
from flask import Flask, jsonify, request
from node.blockchain import Blockchain
from node.transaction import Transaction

app = Flask(__name__)

class NodeAPI:
    def __init__(self, blockchain, network, wallet):
        self.blockchain = blockchain
        self.network = network
        self.wallet = wallet

    def run(self, port):
        self.port = port
        self.app_thread = threading.Thread(target=lambda: app.run(port=port, debug=False, use_reloader=False))
        self.app_thread.start()

    def stop(self):
        # Flask ne s'arrête pas facilement, donc tu devras tuer le process manuellement ou améliorer
        pass

blockchain = Blockchain()
network = None  # sera injecté depuis node.py
wallet = None   # idem

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [block.to_dict() for block in blockchain.chain]
    return jsonify({"length": len(chain_data), "chain": chain_data})

@app.route('/mine', methods=['GET'])
def mine():
    miner_address = request.args.get('miner_address')
    block = blockchain.mine(miner_address)
    if not block:
        return jsonify({"message": "Pas de transactions à miner"}), 400
    return jsonify({"message": "Bloc miné", "block": block.to_dict()})

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["sender", "recipient", "amount"]
    for field in required_fields:
        if field not in tx_data:
            return "Invalid transaction data", 400

    transaction = Transaction(tx_data['sender'], tx_data['recipient'], tx_data['amount'])
    blockchain.add_new_transaction(transaction.to_dict())
    return "Transaction ajoutée", 201

@app.route('/peers', methods=['GET'])
def peers():
    peers = network.get_peers()
    return jsonify({"peers": peers})

@app.route('/balance/<string:address>', methods=['GET'])
def balance(address):
    balance = 0
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx['recipient'] == address:
                balance += tx['amount']
            if tx['sender'] == address:
                balance -= tx['amount']
    return jsonify({"address": address, "balance": balance})
