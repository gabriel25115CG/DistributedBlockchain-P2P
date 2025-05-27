import rsa

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

    def get_public_key_pem(self):
        return self.public_key.save_pkcs1().decode()

    def get_private_key_pem(self):
        return self.private_key.save_pkcs1().decode()
