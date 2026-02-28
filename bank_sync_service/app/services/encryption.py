from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.exceptions import EncryptionError


class TokenEncryption:
    def __init__(self, key: str | None = None):
        try:
            self.fernet = Fernet((key or settings.BANK_TOKEN_ENCRYPTION_KEY).encode())
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {str(e)}")

    def encrypt(self, token: str) -> str:
        try:
            return self.fernet.encrypt(token.encode()).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt token: {str(e)}")

    def decrypt(self, encrypted: str) -> str:
        try:
            return self.fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            raise EncryptionError("Failed to decrypt token: invalid key or corrupted data")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt token: {str(e)}")


# Singleton instance
encryption = TokenEncryption()
