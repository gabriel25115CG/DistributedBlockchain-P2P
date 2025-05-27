import rsa
import hashlib

class Wallet:
    def __init__(self):
        # Génère une paire de clés RSA 512 bits (publique, privée)
        self.public_key, self.private_key = rsa.newkeys(512)

    def sign(self, message: bytes) -> bytes:
        # Signe un message (bytes) avec la clé privée (SHA-256)
        return rsa.sign(message, self.private_key, 'SHA-256')

    def verify(self, message: bytes, signature: bytes, public_key) -> bool:
        # Vérifie la signature d'un message avec la clé publique
        try:
            rsa.verify(message, signature, public_key)
            return True
        except rsa.VerificationError:
            return False

    def get_public_key_pem(self) -> str:
        # Retourne la clé publique au format PEM (string)
        return self.public_key.save_pkcs1().decode()

    def get_private_key_pem(self) -> str:
        # Retourne la clé privée au format PEM (string)
        return self.private_key.save_pkcs1().decode()

    def get_address(self) -> str:
        # Calcule l'adresse en SHA256 de la clé publique PEM (format hex)
        pubkey_pem = self.get_public_key_pem().encode()
        return hashlib.sha256(pubkey_pem).hexdigest()

    def get_balance(self, blockchain, address: str) -> float:
        # Calcule le solde d'une adresse en parcourant la blockchain complète
        balance = 0.0
        for block in blockchain.chain:
            for tx in block.transactions:
                # Attention: Assure-toi que tx est un dict avec 'sender', 'recipient', 'amount'
                sender = tx.get('sender')
                recipient = tx.get('recipient')
                amount = tx.get('amount', 0)

                if recipient == address:
                    balance += amount
                if sender == address:
                    balance -= amount
        return balance
