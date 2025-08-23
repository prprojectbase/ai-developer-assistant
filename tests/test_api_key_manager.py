#!/usr/bin/env python3
"""
API Key Manager Tests

Comprehensive tests for the secure API key management system.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add the src directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.api_key_manager import ApiKeyManager, ApiKeyInfo, get_api_key_manager, initialize_api_key_manager


class TestApiKeyManager(unittest.TestCase):
    """Test cases for ApiKeyManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test.log")
        
        # Create a mock settings object
        self.mock_settings = Mock()
        self.mock_settings.log_file = self.log_file
        
        # Patch the settings module
        self.settings_patcher = patch('src.utils.api_key_manager.get_settings')
        self.mock_get_settings = self.settings_patcher.start()
        self.mock_get_settings.return_value = self.mock_settings
        
        # Initialize key manager with test directory
        self.key_manager = ApiKeyManager()
        
    def tearDown(self):
        """Clean up after tests"""
        self.settings_patcher.stop()
        
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test API key manager initialization"""
        self.assertIsNotNone(self.key_manager.encryption_key)
        self.assertIsNotNone(self.key_manager.cipher_suite)
        self.assertEqual(len(self.key_manager.api_keys), 0)
        self.assertTrue(self.key_manager.key_usage_tracking)
        self.assertEqual(self.key_manager.max_key_age_days, 90)
    
    def test_encryption_decryption(self):
        """Test basic encryption and decryption"""
        test_key = "sk-test-api-key-1234567890"
        
        # Encrypt the key
        encrypted = self.key_manager.encrypt_api_key(test_key)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, test_key)
        
        # Decrypt the key
        decrypted = self.key_manager.decrypt_api_key(encrypted)
        self.assertEqual(decrypted, test_key)
    
    def test_password_based_encryption(self):
        """Test password-based encryption and decryption"""
        test_key = "sk-test-password-protected-key"
        password = "my_secure_password_123"
        
        # Encrypt with password
        encrypted = self.key_manager.encrypt_api_key(test_key, password)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, test_key)
        
        # Decrypt with correct password
        decrypted = self.key_manager.decrypt_api_key(encrypted, password)
        self.assertEqual(decrypted, test_key)
        
        # Try to decrypt without password (should fail)
        with self.assertRaises(Exception):
            self.key_manager.decrypt_api_key(encrypted)
        
        # Try to decrypt with wrong password (should fail)
        with self.assertRaises(Exception):
            self.key_manager.decrypt_api_key(encrypted, "wrong_password")
    
    def test_store_and_retrieve_api_key(self):
        """Test storing and retrieving API keys"""
        test_key = "sk-test-store-retrieve-1234567890"
        service = "test_service"
        
        # Store the key
        key_id = self.key_manager.store_api_key(
            service=service,
            api_key=test_key,
            expires_in_days=30,
            metadata={"test": True}
        )
        
        self.assertIsInstance(key_id, str)
        self.assertIn(key_id, self.key_manager.api_keys)
        
        # Retrieve the key
        retrieved_key = self.key_manager.retrieve_api_key(key_id)
        self.assertEqual(retrieved_key, test_key)
        
        # Check key info
        key_info = self.key_manager.api_keys[key_id]
        self.assertEqual(key_info.service, service)
        self.assertEqual(key_info.key_id, key_id)
        self.assertTrue(key_info.is_active)
        self.assertIsNotNone(key_info.expires_at)
        self.assertEqual(key_info.metadata, {"test": True})
    
    def test_retrieve_nonexistent_key(self):
        """Test retrieving a non-existent key"""
        result = self.key_manager.retrieve_api_key("nonexistent_key")
        self.assertIsNone(result)
    
    def test_retrieve_inactive_key(self):
        """Test retrieving an inactive key"""
        test_key = "sk-test-inactive-key"
        
        # Store the key
        key_id = self.key_manager.store_api_key("test", test_key)
        
        # Deactivate the key
        self.key_manager.api_keys[key_id].is_active = False
        
        # Try to retrieve (should fail)
        result = self.key_manager.retrieve_api_key(key_id)
        self.assertIsNone(result)
    
    def test_retrieve_expired_key(self):
        """Test retrieving an expired key"""
        test_key = "sk-test-expired-key"
        
        # Store the key with expiration in the past
        key_id = self.key_manager.store_api_key("test", test_key, expires_in_days=-1)
        
        # Try to retrieve (should fail)
        result = self.key_manager.retrieve_api_key(key_id)
        self.assertIsNone(result)
    
    def test_list_api_keys(self):
        """Test listing API keys"""
        # Store multiple keys
        key1_id = self.key_manager.store_api_key("service1", "key1")
        key2_id = self.key_manager.store_api_key("service2", "key2")
        key3_id = self.key_manager.store_api_key("service1", "key3")
        
        # List all keys
        all_keys = self.key_manager.list_api_keys()
        self.assertEqual(len(all_keys), 3)
        self.assertIn(key1_id, all_keys)
        self.assertIn(key2_id, all_keys)
        self.assertIn(key3_id, all_keys)
        
        # List keys for specific service
        service1_keys = self.key_manager.list_api_keys("service1")
        self.assertEqual(len(service1_keys), 2)
        self.assertIn(key1_id, service1_keys)
        self.assertIn(key3_id, service1_keys)
        
        service2_keys = self.key_manager.list_api_keys("service2")
        self.assertEqual(len(service2_keys), 1)
        self.assertIn(key2_id, service2_keys)
        
        # Verify keys are not exposed in listing
        for key_info in all_keys.values():
            self.assertNotIn("encrypted_key", key_info)
            self.assertNotIn("key", key_info)
    
    def test_revoke_api_key(self):
        """Test revoking API keys"""
        test_key = "sk-test-revoke-key"
        
        # Store the key
        key_id = self.key_manager.store_api_key("test", test_key)
        
        # Verify key is active
        self.assertTrue(self.key_manager.api_keys[key_id].is_active)
        
        # Revoke the key
        result = self.key_manager.revoke_api_key(key_id)
        self.assertTrue(result)
        self.assertFalse(self.key_manager.api_keys[key_id].is_active)
        
        # Try to retrieve revoked key (should fail)
        retrieved = self.key_manager.retrieve_api_key(key_id)
        self.assertIsNone(retrieved)
        
        # Try to revoke non-existent key
        result = self.key_manager.revoke_api_key("nonexistent")
        self.assertFalse(result)
    
    def test_delete_api_key(self):
        """Test deleting API keys"""
        test_key = "sk-test-delete-key"
        
        # Store the key
        key_id = self.key_manager.store_api_key("test", test_key)
        
        # Verify key exists
        self.assertIn(key_id, self.key_manager.api_keys)
        
        # Delete the key
        result = self.key_manager.delete_api_key(key_id)
        self.assertTrue(result)
        self.assertNotIn(key_id, self.key_manager.api_keys)
        
        # Try to delete non-existent key
        result = self.key_manager.delete_api_key("nonexistent")
        self.assertFalse(result)
    
    def test_rotate_api_key(self):
        """Test rotating API keys"""
        old_key = "sk-test-old-key"
        new_key = "sk-test-new-key"
        
        # Store the original key
        key_id = self.key_manager.store_api_key("test", old_key)
        
        # Rotate the key
        result = self.key_manager.rotate_api_key(key_id, new_key)
        self.assertEqual(result, key_id)
        
        # Verify the key was updated
        retrieved_key = self.key_manager.retrieve_api_key(key_id)
        self.assertEqual(retrieved_key, new_key)
        
        # Verify creation time was updated
        key_info = self.key_manager.api_keys[key_id]
        self.assertGreater(key_info.created_at, datetime.now() - timedelta(seconds=10))
        
        # Try to rotate non-existent key
        result = self.key_manager.rotate_api_key("nonexistent", new_key)
        self.assertIsNone(result)
    
    def test_cleanup_expired_keys(self):
        """Test cleanup of expired keys"""
        # Create an expired key
        expired_key_id = self.key_manager.store_api_key("test", "expired", expires_in_days=-1)
        
        # Create an old inactive key
        old_key_id = self.key_manager.store_api_key("test", "old")
        self.key_manager.api_keys[old_key_id].is_active = False
        self.key_manager.api_keys[old_key_id].created_at = datetime.now() - timedelta(days=35)
        
        # Create a valid key
        valid_key_id = self.key_manager.store_api_key("test", "valid")
        
        # Run cleanup
        cleaned_count = self.key_manager.cleanup_expired_keys()
        self.assertEqual(cleaned_count, 2)
        
        # Verify expired and old keys were deleted
        self.assertNotIn(expired_key_id, self.key_manager.api_keys)
        self.assertNotIn(old_key_id, self.key_manager.api_keys)
        
        # Verify valid key still exists
        self.assertIn(valid_key_id, self.key_manager.api_keys)
    
    def test_key_format_validation(self):
        """Test API key format validation"""
        # Valid keys
        valid_cases = [
            ("sk-or-v1-1234567890abcdef", "openrouter"),
            ("sk-1234567890abcdef1234567890abcdef", "openai"),
            ("AIza1234567890abcdef1234567890abcdef", "google"),
            ("sk-ant-1234567890abcdef", "anthropic")
        ]
        
        for key, service in valid_cases:
            result = self.key_manager.validate_api_key_format(key, service)
            self.assertTrue(result, f"Key {key} should be valid for {service}")
        
        # Invalid keys
        invalid_cases = [
            ("invalid", "openrouter"),
            ("short", "openai"),
            ("", "google"),
            ("sk-or-v1", "openrouter"),  # Too short
            ("not-a-key", "unknown_service")
        ]
        
        for key, service in invalid_cases:
            result = self.key_manager.validate_api_key_format(key, service)
            self.assertFalse(result, f"Key {key} should be invalid for {service}")
    
    def test_security_audit(self):
        """Test security audit functionality"""
        # Create various keys for testing
        active_key_id = self.key_manager.store_api_key("test", "active")
        expired_key_id = self.key_manager.store_api_key("test", "expired", expires_in_days=-1)
        old_key_id = self.key_manager.store_api_key("test", "old")
        self.key_manager.api_keys[old_key_id].created_at = datetime.now() - timedelta(days=100)
        no_expiration_key_id = self.key_manager.store_api_key("test", "no_expiration")
        self.key_manager.api_keys[no_expiration_key_id].expires_at = None
        
        # Get security audit
        audit = self.key_manager.get_key_security_audit()
        
        self.assertEqual(audit["total_keys"], 4)
        self.assertEqual(audit["active_keys"], 2)  # active_key_id and no_expiration_key_id
        self.assertEqual(audit["expired_keys"], 1)  # expired_key_id
        self.assertEqual(audit["old_keys"], 1)  # old_key_id
        self.assertEqual(audit["keys_without_expiration"], 1)  # no_expiration_key_id
        self.assertTrue(audit["encryption_enabled"])
        self.assertIsInstance(audit["security_recommendations"], list)
    
    def test_save_and_load_keys(self):
        """Test saving and loading keys to/from file"""
        # Store some keys
        key1_id = self.key_manager.store_api_key("service1", "key1", expires_in_days=30)
        key2_id = self.key_manager.store_api_key("service2", "key2")
        
        # Save keys
        self.key_manager._save_keys()
        self.assertTrue(os.path.exists(self.key_manager.key_storage_file))
        
        # Create new key manager instance
        new_key_manager = ApiKeyManager()
        
        # Verify keys were loaded
        self.assertEqual(len(new_key_manager.api_keys), 2)
        self.assertIn(key1_id, new_key_manager.api_keys)
        self.assertIn(key2_id, new_key_manager.api_keys)
        
        # Verify keys can be retrieved
        retrieved_key1 = new_key_manager.retrieve_api_key(key1_id)
        retrieved_key2 = new_key_manager.retrieve_api_key(key2_id)
        
        self.assertEqual(retrieved_key1, "key1")
        self.assertEqual(retrieved_key2, "key2")
    
    def test_change_encryption_key(self):
        """Test changing the master encryption key"""
        # Store a key
        key_id = self.key_manager.store_api_key("test", "test_key")
        
        # Generate new encryption key
        new_key = self.key_manager._get_or_create_encryption_key()
        
        # Change encryption key
        self.key_manager.change_encryption_key(new_key)
        
        # Verify the key can still be retrieved
        retrieved_key = self.key_manager.retrieve_api_key(key_id)
        self.assertEqual(retrieved_key, "test_key")
    
    def test_key_id_generation(self):
        """Test key ID generation"""
        service = "test_service"
        
        # Generate multiple key IDs
        key_id1 = self.key_manager._generate_key_id(service)
        key_id2 = self.key_manager._generate_key_id(service)
        
        # Verify IDs are unique
        self.assertNotEqual(key_id1, key_id2)
        
        # Verify IDs contain service name
        self.assertIn(service, key_id1)
        self.assertIn(service, key_id2)
        
        # Verify IDs contain timestamp
        self.assertIn(datetime.now().strftime("%Y%m%d"), key_id1)
        self.assertIn(datetime.now().strftime("%Y%m%d"), key_id2)


class TestApiKeyInfo(unittest.TestCase):
    """Test cases for ApiKeyInfo dataclass"""
    
    def test_key_info_creation(self):
        """Test ApiKeyInfo creation"""
        key_info = ApiKeyInfo(
            service="test_service",
            key_id="test_key_id",
            encrypted_key="encrypted_data",
            expires_at=datetime.now() + timedelta(days=30),
            metadata={"test": True}
        )
        
        self.assertEqual(key_info.service, "test_service")
        self.assertEqual(key_info.key_id, "test_key_id")
        self.assertEqual(key_info.encrypted_key, "encrypted_data")
        self.assertTrue(key_info.is_active)
        self.assertIsNotNone(key_info.expires_at)
        self.assertEqual(key_info.metadata, {"test": True})
        self.assertIsInstance(key_info.created_at, datetime)


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear global instance
        import src.utils.api_key_manager
        src.utils.api_key_manager._api_key_manager = None
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear global instance
        import src.utils.api_key_manager
        src.utils.api_key_manager._api_key_manager = None
    
    def test_get_api_key_manager(self):
        """Test getting global API key manager instance"""
        # First call should create instance
        manager1 = get_api_key_manager()
        self.assertIsInstance(manager1, ApiKeyManager)
        
        # Second call should return same instance
        manager2 = get_api_key_manager()
        self.assertIs(manager1, manager2)
    
    def test_initialize_api_key_manager(self):
        """Test initializing API key manager with custom key"""
        custom_key = b"custom_encryption_key_1234567890"
        
        # Initialize with custom key
        manager = initialize_api_key_manager(custom_key)
        self.assertIsInstance(manager, ApiKeyManager)
        self.assertEqual(manager.encryption_key, custom_key)
        
        # Verify global instance is set
        global_manager = get_api_key_manager()
        self.assertIs(global_manager, manager)


if __name__ == '__main__':
    # Run the tests
    unittest.main()