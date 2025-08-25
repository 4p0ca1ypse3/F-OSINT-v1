"""
Encryption utilities for F-OSINT DWv1
"""

import os
import base64
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordManager:
    """Secure password management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class DataEncryption:
    """Data encryption and decryption"""
    
    def __init__(self, password: str = None):
        if password:
            self.key = self._derive_key(password)
            self.cipher = Fernet(self.key)
        else:
            self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password"""
        if salt is None:
            salt = b'f-osint-salt-2025'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary data"""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt dictionary data"""
        import json
        json_str = self.decrypt(encrypted_data)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_key(self) -> str:
        """Get the encryption key as string"""
        return base64.urlsafe_b64encode(self.key).decode()


def generate_session_token() -> str:
    """Generate a secure session token"""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def generate_api_key() -> str:
    """Generate a secure API key"""
    return base64.urlsafe_b64encode(os.urandom(48)).decode()


def secure_compare(a: str, b: str) -> bool:
    """Securely compare two strings to prevent timing attacks"""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0