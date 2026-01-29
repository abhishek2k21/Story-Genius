"""
Field-Level Encryption for PII Data.
Encrypts sensitive fields like email, phone, SSN, credit card, etc.
"""
from cryptography.fernet import Fernet
from app.core.vault_client import get_vault_client
from typing import Optional
import base64
import logging

logger = logging.getLogger(__name__)


class FieldEncryption:
    """
    Field-level encryption for PII data.
    Uses AES-256 via Fernet (symmetric encryption).
    Keys stored securely in HashiCorp Vault.
    """
    
    def __init__(self):
        """Initialize field encryption with key from Vault."""
        self.vault = get_vault_client()
        self._load_encryption_key()
    
    def _load_encryption_key(self):
        """Load or generate encryption key from Vault."""
        try:
            # Try to get existing key
            secret = self.vault.get_secret("encryption/field-key")
            self.key = secret["key"].encode()
            logger.info("Loaded field encryption key from Vault")
        
        except Exception as e:
            # Generate new key if not exists
            logger.info(f"Generating new field encryption key: {e}")
            self.key = Fernet.generate_key()
            
            # Store in Vault
            self.vault.set_secret("encryption/field-key", {
                "key": self.key.decode()
            })
            logger.info("Generated and stored new field encryption key")
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt sensitive field.
        
        Args:
            plaintext: Plain text to encrypt
            
        Returns:
            Base64-encoded ciphertext
        """
        if not plaintext:
            return plaintext
        
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt sensitive field.
        
        Args:
            ciphertext: Base64-encoded ciphertext
            
        Returns:
            Decrypted plaintext
        """
        if not ciphertext:
            return ciphertext
        
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_email(self, email: str) -> str:
        """Encrypt email address."""
        return self.encrypt(email)
    
    def decrypt_email(self, encrypted_email: str) -> str:
        """Decrypt email address."""
        return self.decrypt(encrypted_email)
    
    def encrypt_phone(self, phone: str) -> str:
        """Encrypt phone number."""
        return self.encrypt(phone)
    
    def decrypt_phone(self, encrypted_phone: str) -> str:
        """Decrypt phone number."""
        return self.decrypt(encrypted_phone)
    
    def encrypt_ssn(self, ssn: str) -> str:
        """Encrypt SSN."""
        return self.encrypt(ssn)
    
    def decrypt_ssn(self, encrypted_ssn: str) -> str:
        """Decrypt SSN."""
        return self.decrypt(encrypted_ssn)
    
    def encrypt_credit_card(self, cc: str) -> str:
        """Encrypt credit card number."""
        return self.encrypt(cc)
    
    def decrypt_credit_card(self, encrypted_cc: str) -> str:
        """Decrypt credit card number."""
        return self.decrypt(encrypted_cc)


# Singleton instance
_field_encryption: Optional[FieldEncryption] = None


def get_field_encryption() -> FieldEncryption:
    """Get singleton field encryption instance."""
    global _field_encryption
    
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    
    return _field_encryption


# Example usage in models
class EncryptedField:
    """
    SQLAlchemy custom type for encrypted fields.
    Transparently encrypts/decrypts data.
    """
    
    def __init__(self):
        self.encryption = get_field_encryption()
    
    def process_bind_param(self, value, dialect):
        """Encrypt before storing in database."""
        if value is not None:
            return self.encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """Decrypt when retrieving from database."""
        if value is not None:
            return self.encryption.decrypt(value)
        return value


# Usage in SQLAlchemy models:
"""
from sqlalchemy import TypeDecorator, String

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encryption = get_field_encryption()
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return self.encryption.decrypt(value)
        return value

# In model:
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(EncryptedString(255))  # Encrypted in database
    phone = Column(EncryptedString(255))  # Encrypted in database
"""
