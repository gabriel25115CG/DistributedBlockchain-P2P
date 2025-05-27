import time
from node.block import Block
from node.transaction import Transaction
from config import DIFFICULTY, MINING_REWARD

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []  # transactions non minées
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", time.time(), [])
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * DIFFICULTY):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        return (block_hash.startswith('0' * DIFFICULTY) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self, miner_address):
        if not self.unconfirmed_transactions:
            return False

        # Ajouter la récompense de minage
        reward_tx = Transaction("Network", miner_address, MINING_REWARD)
        transactions = self.unconfirmed_transactions + [reward_tx.to_dict()]
        
        new_block = Block(index=self.last_block.index + 1,
                          previous_hash=self.last_block.hash,
                          timestamp=time.time(),
                          transactions=transactions)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block
