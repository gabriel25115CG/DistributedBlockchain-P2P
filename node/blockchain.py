import time
from node.block import Block
from node.transaction import Transaction
from config import DIFFICULTY, MINING_REWARD

class Blockchain:

    def __init__(self):
        self.chain = []
        self.unconfirmed_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=0,
            previous_hash='0'
        )
        genesis_block.nonce = 0
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

        # Vérifie que le précédent hash correspond
        if previous_hash != block.previous_hash:
            print("Erreur : previous_hash ne correspond pas")
            return False

        # Vérifie la validité du proof-of-work
        if not self.is_valid_proof(block, proof):
            print("Erreur : preuve de travail invalide")
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        return (block_hash.startswith('0' * DIFFICULTY) and
                block_hash == block.compute_hash())

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx['recipient'] == address:
                    balance += tx['amount']
                if tx['sender'] == address:
                    balance -= tx['amount']
        return balance

    def add_new_transaction(self, transaction):
        sender = transaction['sender']
        amount = transaction['amount']

        if sender != "Network":  # Les transactions réseau (récompenses) sont toujours valides
            sender_balance = self.get_balance(sender)
            # Montant des transactions en attente envoyées par le sender
            pending_amount = sum(
                tx['amount'] for tx in self.unconfirmed_transactions if tx['sender'] == sender
            )
            available_balance = sender_balance - pending_amount

            if available_balance < amount:
                print(f"Erreur : Solde insuffisant pour la transaction de {amount} UTBM envoyée par {sender}")
                return False

        self.unconfirmed_transactions.append(transaction)
        return True

    def mine(self, miner_address, network=None):
        if not self.unconfirmed_transactions:
            print("Aucune transaction à miner")
            return None

        reward_tx = Transaction("Network", miner_address, MINING_REWARD)

        transactions = list(self.unconfirmed_transactions) + [reward_tx.to_dict()]

        new_block = Block(
            index=self.last_block.index + 1,
            previous_hash=self.last_block.hash,
            timestamp=time.time(),
            transactions=transactions
        )

        proof = self.proof_of_work(new_block)

        if self.add_block(new_block, proof):
            self.unconfirmed_transactions = []

            # Propager le bloc miné aux peers si un réseau est fourni
            if network:
                for peer in network.get_peers():
                    try:
                        network.send_block(peer, new_block)
                    except Exception as e:
                        print(f"Erreur propagation bloc vers peer {peer}: {e}")

            return new_block
        else:
            print("Erreur lors de l'ajout du bloc miné à la chaîne")
            return None

    def add_block_from_network(self, block_data, network=None):
        """
        Ajoute un bloc reçu du réseau après validation.
        Si rejeté à cause du previous_hash, tente une synchronisation.
        """
        block = Block.from_dict(block_data)
        proof = block.hash

        if block.previous_hash != self.last_block.hash:
            print(f"Erreur : previous_hash ne correspond pas")
            print(f"Reçu :     {block.previous_hash}")
            print(f"Attendu :  {self.last_block.hash}")
            return False

        if self.add_block(block, proof):
            # Nettoyer les transactions confirmées
            tx_hashes = set(
                Transaction(tx['sender'], tx['recipient'], tx['amount']).compute_hash()
                for tx in block.transactions
            )
            self.unconfirmed_transactions = [
                tx for tx in self.unconfirmed_transactions
                if Transaction(tx['sender'], tx['recipient'], tx['amount']).compute_hash() not in tx_hashes
            ]
            print(f"Bloc ajouté depuis le réseau : index {block.index}")
            return True
        else:
            print(f"Bloc rejeté depuis le réseau : index {block.index}")
            # Si réseau disponible, tenter de synchroniser la chaîne complète
            if network:
                for peer in network.get_peers():
                    if self.sync_chain_from_peer(peer):
                        print("Chaîne synchronisée après rejet de bloc")
                        return True
            return False

    def is_valid_chain(self, chain):
        """
        Vérifie que la chaîne est valide
        """
        if not chain:
            return False

        # Vérifie le bloc genesis
        genesis = chain[0]
        if genesis.hash != genesis.compute_hash():
            return False

        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            if current.previous_hash != previous.hash:
                return False
            if not self.is_valid_proof(current, current.hash):
                return False
        return True

    def replace_chain(self, new_chain):
        """
        Remplace la chaîne locale par une nouvelle si elle est plus longue et valide
        """
        if len(new_chain) <= len(self.chain):
            print("La chaîne distante est plus courte ou égale, remplacement ignoré.")
            return False

        if not self.is_valid_chain(new_chain):
            print("La chaîne distante n'est pas valide.")
            return False

        self.chain = new_chain
        print("Chaîne locale remplacée par la chaîne distante.")
        return True

    def sync_chain_from_peer(self, peer):
        """
        Tente de synchroniser la chaîne avec un peer.
        network doit fournir une méthode pour récupérer la chaîne complète.
        """
        try:
            chain_data = peer.request_chain()  # Cette méthode doit être définie dans l'objet peer
            new_chain = [Block.from_dict(b) for b in chain_data]
            if self.replace_chain(new_chain):
                return True
        except Exception as e:
            print(f"Erreur synchronisation chaîne avec peer {peer}: {e}")
        return False
