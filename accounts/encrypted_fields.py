"""
Custom encrypted field implementation for Django 5.0 compatibility.
Uses Fernet symmetric encryption from the cryptography library.
"""
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib


def get_encryption_key():
    """
    Derive encryption key from Django SECRET_KEY.
    """
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


class EncryptedCharField(models.CharField):
    """
    CharField that automatically encrypts/decrypts values using Fernet.
    """
    description = "Encrypted CharField"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fernet = Fernet(get_encryption_key())
    
    def get_prep_value(self, value):
        """Encrypt value before saving to database"""
        if value is None or value == '':
            return value
        
        if isinstance(value, str):
            encrypted = self.fernet.encrypt(value.encode())
            return encrypted.decode('utf-8')
        return value
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when loading from database"""
        if value is None or value == '':
            return value
        
        try:
            decrypted = self.fernet.decrypt(value.encode())
            return decrypted.decode('utf-8')
        except Exception:
            return value
    
    def to_python(self, value):
        """Convert to Python value"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
