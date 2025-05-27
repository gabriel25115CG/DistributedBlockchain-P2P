import json
import hashlib

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def to_dict(self):
        return self.__dict__

    def compute_hash(self):
        tx_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_str.encode()).hexdigest()
