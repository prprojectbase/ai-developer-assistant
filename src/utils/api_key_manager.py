import os
import logging
import json
import base64
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib

from ..config.settings import get_settings


@dataclass
class ApiKeyInfo:
    """API key information structure"""
    service: str
    key_id: str
    encrypted_key: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


class ApiKeyManager:
    """Secure API key management with encryption"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self.encryption_key = encryption_key or self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # API key storage
        self.api_keys: Dict[str, ApiKeyInfo] = {}
        self.key_storage_file = os.path.join(
            os.path.dirname(self.settings.log_file), 
            "api_keys.enc"
        )
        
        # Security settings
        self.max_key_age_days = 90
        self.auto_rotate_keys = True
        self.key_usage_tracking = True
        
        # Load existing keys
        self._load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API key storage"""
        key_file = os.path.join(
            os.path.dirname(self.settings.log_file), 
            "encryption.key"
        )
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error reading encryption key: {e}")
        
        # Generate new encryption key
        key = Fernet.generate_key()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            
            # Save key with restricted permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set file permissions (read/write only for owner)
            os.chmod(key_file, 0o600)
            
            self.logger.info("Created new encryption key")
            return key
            
        except Exception as e:
            self.logger.error(f"Error creating encryption key: {e}")
            raise
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_api_key(self, api_key: str, password: Optional[str] = None) -> str:
        """Encrypt an API key"""
        try:
            if password:
                # Use password-based encryption
                salt = os.urandom(16)
                key = self._derive_key_from_password(password, salt)
                cipher = Fernet(key)
                encrypted = cipher.encrypt(api_key.encode())
                # Combine salt and encrypted data
                return base64.urlsafe_b64encode(salt + encrypted).decode()
            else:
                # Use master encryption key
                return self.cipher_suite.encrypt(api_key.encode()).decode()
                
        except Exception as e:
            self.logger.error(f"Error encrypting API key: {e}")
            raise
    
    def decrypt_api_key(self, encrypted_key: str, password: Optional[str] = None) -> str:
        """Decrypt an API key"""
        try:
            if password:
                # Use password-based decryption
                data = base64.urlsafe_b64decode(encrypted_key.encode())
                salt = data[:16]
                encrypted = data[16:]
                key = self._derive_key_from_password(password, salt)
                cipher = Fernet(key)
                return cipher.decrypt(encrypted).decode()
            else:
                # Use master encryption key
                return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
                
        except Exception as e:
            self.logger.error(f"Error decrypting API key: {e}")
            raise
    
    def store_api_key(self, service: str, api_key: str, password: Optional[str] = None,
                     expires_in_days: Optional[int] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store an encrypted API key"""
        try:
            # Generate key ID
            key_id = self._generate_key_id(service)
            
            # Encrypt the API key
            encrypted_key = self.encrypt_api_key(api_key, password)
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create key info
            key_info = ApiKeyInfo(
                service=service,
                key_id=key_id,
                encrypted_key=encrypted_key,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Store the key
            self.api_keys[key_id] = key_info
            
            # Save to file
            self._save_keys()
            
            self.logger.info(f"Stored API key for service: {service}")
            return key_id
            
        except Exception as e:
            self.logger.error(f"Error storing API key: {e}")
            raise
    
    def retrieve_api_key(self, key_id: str, password: Optional[str] = None) -> Optional[str]:
        """Retrieve and decrypt an API key"""
        try:
            if key_id not in self.api_keys:
                self.logger.warning(f"API key not found: {key_id}")
                return None
            
            key_info = self.api_keys[key_id]
            
            # Check if key is active
            if not key_info.is_active:
                self.logger.warning(f"API key is inactive: {key_id}")
                return None
            
            # Check expiration
            if key_info.expires_at and datetime.now() > key_info.expires_at:
                self.logger.warning(f"API key has expired: {key_id}")
                return None
            
            # Decrypt the key
            api_key = self.decrypt_api_key(key_info.encrypted_key, password)
            
            # Update last used timestamp
            if self.key_usage_tracking:
                key_info.last_used = datetime.now()
                self._save_keys()
            
            return api_key
            
        except Exception as e:
            self.logger.error(f"Error retrieving API key: {e}")
            return None
    
    def list_api_keys(self, service: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """List stored API keys (without exposing the actual keys)"""
        result = {}
        
        for key_id, key_info in self.api_keys.items():
            if service and key_info.service != service:
                continue
            
            result[key_id] = {
                "service": key_info.service,
                "created_at": key_info.created_at.isoformat(),
                "expires_at": key_info.expires_at.isoformat() if key_info.expires_at else None,
                "last_used": key_info.last_used.isoformat() if key_info.last_used else None,
                "is_active": key_info.is_active,
                "metadata": key_info.metadata,
                "is_expired": key_info.expires_at and datetime.now() > key_info.expires_at,
                "age_days": (datetime.now() - key_info.created_at).days
            }
        
        return result
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        try:
            if key_id not in self.api_keys:
                self.logger.warning(f"API key not found: {key_id}")
                return False
            
            self.api_keys[key_id].is_active = False
            self._save_keys()
            
            self.logger.info(f"Revoked API key: {key_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking API key: {e}")
            return False
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key permanently"""
        try:
            if key_id not in self.api_keys:
                self.logger.warning(f"API key not found: {key_id}")
                return False
            
            del self.api_keys[key_id]
            self._save_keys()
            
            self.logger.info(f"Deleted API key: {key_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting API key: {e}")
            return False
    
    def rotate_api_key(self, key_id: str, new_api_key: str, password: Optional[str] = None) -> Optional[str]:
        """Rotate an API key"""
        try:
            if key_id not in self.api_keys:
                self.logger.warning(f"API key not found: {key_id}")
                return None
            
            key_info = self.api_keys[key_id]
            
            # Encrypt new key
            new_encrypted_key = self.encrypt_api_key(new_api_key, password)
            
            # Update key info
            key_info.encrypted_key = new_encrypted_key
            key_info.created_at = datetime.now()
            
            # Reset expiration if set
            if key_info.expires_at:
                key_info.expires_at = datetime.now() + timedelta(days=self.max_key_age_days)
            
            self._save_keys()
            
            self.logger.info(f"Rotated API key: {key_id}")
            return key_id
            
        except Exception as e:
            self.logger.error(f"Error rotating API key: {e}")
            return None
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired and inactive keys"""
        try:
            keys_to_delete = []
            now = datetime.now()
            
            for key_id, key_info in self.api_keys.items():
                # Delete expired keys older than max_key_age_days
                if (key_info.expires_at and now > key_info.expires_at and 
                    (now - key_info.expires_at).days > 7):
                    keys_to_delete.append(key_id)
                
                # Delete inactive keys older than 30 days
                elif (not key_info.is_active and 
                      (now - key_info.created_at).days > 30):
                    keys_to_delete.append(key_id)
            
            # Delete keys
            for key_id in keys_to_delete:
                del self.api_keys[key_id]
            
            if keys_to_delete:
                self._save_keys()
                self.logger.info(f"Cleaned up {len(keys_to_delete)} expired/inactive keys")
            
            return len(keys_to_delete)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired keys: {e}")
            return 0
    
    def validate_api_key_format(self, api_key: str, service: str) -> bool:
        """Validate API key format for specific services"""
        # Basic validation patterns for common services
        patterns = {
            "openrouter": r"^sk-or-[a-zA-Z0-9_-]{20,}$",
            "openai": r"^sk-[a-zA-Z0-9_-]{48,}$",
            "anthropic": r"^sk-ant-[a-zA-Z0-9_-]{20,}$",
            "google": r"^AIza[0-9A-Za-z_-]{35}$",
            "default": r"^[a-zA-Z0-9_\-\.]{10,}$"
        }
        
        import re
        pattern = patterns.get(service.lower(), patterns["default"])
        return bool(re.match(pattern, api_key))
    
    def get_key_security_audit(self) -> Dict[str, Any]:
        """Get security audit information for API keys"""
        try:
            now = datetime.now()
            total_keys = len(self.api_keys)
            active_keys = sum(1 for k in self.api_keys.values() if k.is_active)
            expired_keys = sum(1 for k in self.api_keys.values() 
                             if k.expires_at and now > k.expires_at)
            
            old_keys = sum(1 for k in self.api_keys.values() 
                          if (now - k.created_at).days > self.max_key_age_days)
            
            keys_without_expiration = sum(1 for k in self.api_keys.values() 
                                        if not k.expires_at)
            
            return {
                "total_keys": total_keys,
                "active_keys": active_keys,
                "expired_keys": expired_keys,
                "old_keys": old_keys,
                "keys_without_expiration": keys_without_expiration,
                "max_key_age_days": self.max_key_age_days,
                "auto_rotate_enabled": self.auto_rotate_keys,
                "encryption_enabled": True,
                "key_storage_file": self.key_storage_file,
                "security_recommendations": self._get_security_recommendations(
                    total_keys, expired_keys, old_keys, keys_without_expiration
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error getting security audit: {e}")
            return {"error": str(e)}
    
    def _get_security_recommendations(self, total_keys: int, expired_keys: int, 
                                   old_keys: int, no_expiration: int) -> List[str]:
        """Get security recommendations based on audit results"""
        recommendations = []
        
        if expired_keys > 0:
            recommendations.append(f"Revoke or delete {expired_keys} expired API keys")
        
        if old_keys > 0:
            recommendations.append(f"Consider rotating {old_keys} old API keys")
        
        if no_expiration > 0:
            recommendations.append(f"Set expiration dates for {no_expiration} keys without expiration")
        
        if total_keys > 10:
            recommendations.append("Review and remove unused API keys")
        
        if not self.auto_rotate_keys:
            recommendations.append("Enable automatic key rotation")
        
        return recommendations
    
    def _generate_key_id(self, service: str) -> str:
        """Generate a unique key ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = os.urandom(4).hex()
        return f"{service}_{timestamp}_{random_part}"
    
    def _save_keys(self) -> None:
        """Save API keys to encrypted file"""
        try:
            # Prepare data for serialization
            serializable_keys = {}
            for key_id, key_info in self.api_keys.items():
                serializable_keys[key_id] = {
                    "service": key_info.service,
                    "key_id": key_info.key_id,
                    "encrypted_key": key_info.encrypted_key,
                    "created_at": key_info.created_at.isoformat(),
                    "expires_at": key_info.expires_at.isoformat() if key_info.expires_at else None,
                    "last_used": key_info.last_used.isoformat() if key_info.last_used else None,
                    "metadata": key_info.metadata,
                    "is_active": key_info.is_active
                }
            
            # Encrypt the entire data structure
            data_json = json.dumps(serializable_keys, indent=2)
            encrypted_data = self.cipher_suite.encrypt(data_json.encode())
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.key_storage_file), exist_ok=True)
            
            # Save with restricted permissions
            with open(self.key_storage_file, 'wb') as f:
                f.write(encrypted_data)
            
            os.chmod(self.key_storage_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"Error saving API keys: {e}")
            raise
    
    def _load_keys(self) -> None:
        """Load API keys from encrypted file"""
        try:
            if not os.path.exists(self.key_storage_file):
                return
            
            # Read encrypted data
            with open(self.key_storage_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            data_json = self.cipher_suite.decrypt(encrypted_data).decode()
            serializable_keys = json.loads(data_json)
            
            # Reconstruct key info objects
            for key_id, key_data in serializable_keys.items():
                self.api_keys[key_id] = ApiKeyInfo(
                    service=key_data["service"],
                    key_id=key_data["key_id"],
                    encrypted_key=key_data["encrypted_key"],
                    created_at=datetime.fromisoformat(key_data["created_at"]),
                    expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data["expires_at"] else None,
                    last_used=datetime.fromisoformat(key_data["last_used"]) if key_data["last_used"] else None,
                    metadata=key_data["metadata"],
                    is_active=key_data["is_active"]
                )
            
            self.logger.info(f"Loaded {len(self.api_keys)} API keys from storage")
            
        except Exception as e:
            self.logger.error(f"Error loading API keys: {e}")
            # Don't raise here to allow the application to start with empty key storage
    
    def change_encryption_key(self, new_key: bytes) -> None:
        """Change the master encryption key and re-encrypt all stored keys"""
        try:
            # Create new cipher suite
            new_cipher = Fernet(new_key)
            
            # Re-encrypt all keys
            for key_info in self.api_keys.values():
                # Decrypt with old key
                decrypted_key = self.cipher_suite.decrypt(key_info.encrypted_key.encode())
                # Encrypt with new key
                key_info.encrypted_key = new_cipher.encrypt(decrypted_key).decode()
            
            # Update cipher suite
            self.cipher_suite = new_cipher
            self.encryption_key = new_key
            
            # Save re-encrypted keys
            self._save_keys()
            
            # Save new encryption key
            key_file = os.path.join(
                os.path.dirname(self.settings.log_file), 
                "encryption.key"
            )
            with open(key_file, 'wb') as f:
                f.write(new_key)
            os.chmod(key_file, 0o600)
            
            self.logger.info("Successfully changed encryption key and re-encrypted all API keys")
            
        except Exception as e:
            self.logger.error(f"Error changing encryption key: {e}")
            raise


# Global API key manager instance
_api_key_manager: Optional[ApiKeyManager] = None


def get_api_key_manager() -> ApiKeyManager:
    """Get the global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = ApiKeyManager()
    return _api_key_manager


def initialize_api_key_manager(encryption_key: Optional[str] = None) -> ApiKeyManager:
    """Initialize the API key manager with optional custom encryption key"""
    global _api_key_manager
    _api_key_manager = ApiKeyManager(encryption_key)
    return _api_key_manager