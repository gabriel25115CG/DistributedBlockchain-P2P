import rsa
import hashlib

class Wallet:
    def __init__(self):

        self.public_key, self.private_key = rsa.newkeys(512)

    def sign(self, message: bytes) -> bytes:

        return rsa.sign(message, self.private_key, 'SHA-256')

    def verify(self, message: bytes, signature: bytes, public_key) -> bool:

        try:
            rsa.verify(message, signature, public_key)
            return True
        except rsa.VerificationError:
            return False

    def get_public_key_pem(self) -> str:

        return self.public_key.save_pkcs1().decode()

    def get_private_key_pem(self) -> str:

        return self.private_key.save_pkcs1().decode()

    def get_address(self) -> str:

        pubkey_pem = self.get_public_key_pem().encode()
        return hashlib.sha256(pubkey_pem).hexdigest()

    def get_balance(self, blockchain, address: str) -> float:

        balance = 0.0
        for block in blockchain.chain:
            for tx in block.transactions:

                sender = tx.get('sender')
                recipient = tx.get('recipient')
                amount = tx.get('amount', 0)

                if recipient == address:
                    balance += amount
                if sender == address:
                    balance -= amount
        return balance
