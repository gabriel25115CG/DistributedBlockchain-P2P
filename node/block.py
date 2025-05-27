import json
import hashlib

class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions  # liste de dicts
        self.nonce = nonce
        self.hash = None

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nonce": self.nonce
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'nonce': self.nonce,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, block_data):
        block = cls(
            block_data['index'],
            block_data['previous_hash'],
            block_data['timestamp'],
            block_data['transactions'],
            block_data['nonce']
        )
        block.hash = block_data.get('hash')
        return block
