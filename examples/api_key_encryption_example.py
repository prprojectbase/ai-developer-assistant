#!/usr/bin/env python3
"""
API Key Encryption Example

This example demonstrates how to use the secure API key management system
to store, retrieve, and manage API keys with encryption.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta

# Add the src directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.api_key_manager import ApiKeyManager, get_api_key_manager
from config.settings import store_openrouter_api_key, get_openrouter_api_key


async def main():
    """Main example function"""
    print("🔐 AI Developer Assistant - API Key Encryption Example")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize API key manager
    print("📋 Initializing API Key Manager...")
    key_manager = get_api_key_manager()
    
    try:
        # Example API key (in real use, this would come from user input or environment)
        example_api_key = "sk-or-example-v1-1234567890abcdef1234567890abcdef"
        
        print(f"\n🔑 Example API Key: {example_api_key[:20]}...")
        
        # 1. Store API key securely
        print("\n💾 Storing API key securely...")
        key_id = key_manager.store_api_key(
            service="openrouter",
            api_key=example_api_key,
            expires_in_days=30,
            metadata={
                "environment": "example",
                "created_by": "encryption_example",
                "purpose": "demonstration"
            }
        )
        print(f"✅ API key stored with ID: {key_id}")
        
        # 2. List stored keys (without exposing actual keys)
        print("\n📋 Listing stored API keys...")
        stored_keys = key_manager.list_api_keys("openrouter")
        
        for kid, key_info in stored_keys.items():
            print(f"\nKey ID: {kid}")
            print(f"  Service: {key_info['service']}")
            print(f"  Created: {key_info['created_at']}")
            print(f"  Expires: {key_info['expires_at']}")
            print(f"  Active: {key_info['is_active']}")
            print(f"  Age: {key_info['age_days']} days")
            print(f"  Metadata: {key_info['metadata']}")
        
        # 3. Retrieve and decrypt API key
        print(f"\n🔍 Retrieving API key with ID: {key_id}...")
        retrieved_key = key_manager.retrieve_api_key(key_id)
        
        if retrieved_key:
            print(f"✅ Successfully retrieved API key: {retrieved_key[:20]}...")
            print(f"✅ Keys match: {retrieved_key == example_api_key}")
        else:
            print("❌ Failed to retrieve API key")
        
        # 4. Test password-protected encryption
        print("\n🔒 Testing password-protected encryption...")
        password = "my_secure_password_123"
        
        # Store with password protection
        protected_key_id = key_manager.store_api_key(
            service="openrouter",
            api_key="sk-or-protected-v1-abcdef1234567890",
            password=password,
            expires_in_days=60,
            metadata={"protected": True, "encryption": "password_based"}
        )
        print(f"✅ Password-protected key stored with ID: {protected_key_id}")
        
        # Try to retrieve without password (should fail)
        print("🔍 Attempting to retrieve without password...")
        no_password_result = key_manager.retrieve_api_key(protected_key_id)
        print(f"❌ Result without password: {no_password_result}")
        
        # Retrieve with correct password
        print("🔍 Retrieving with correct password...")
        with_password_result = key_manager.retrieve_api_key(protected_key_id, password)
        if with_password_result:
            print(f"✅ Successfully retrieved with password: {with_password_result[:20]}...")
        else:
            print("❌ Failed to retrieve with password")
        
        # 5. Test key rotation
        print("\n🔄 Testing key rotation...")
        new_api_key = "sk-or-rotated-v1-9876543210fedcba9876543210fedcba"
        
        rotation_result = key_manager.rotate_api_key(key_id, new_api_key)
        if rotation_result:
            print("✅ Key rotation successful")
            
            # Verify the rotated key
            rotated_key = key_manager.retrieve_api_key(key_id)
            if rotated_key == new_api_key:
                print("✅ Rotated key verified successfully")
            else:
                print("❌ Rotated key verification failed")
        else:
            print("❌ Key rotation failed")
        
        # 6. Test key revocation
        print("\n🚫 Testing key revocation...")
        revoke_result = key_manager.revoke_api_key(protected_key_id)
        if revoke_result:
            print("✅ Key revoked successfully")
            
            # Try to retrieve revoked key (should fail)
            revoked_key = key_manager.retrieve_api_key(protected_key_id)
            if revoked_key is None:
                print("✅ Revoked key cannot be retrieved (as expected)")
            else:
                print("❌ Revoked key was still accessible")
        else:
            print("❌ Key revocation failed")
        
        # 7. Test security audit
        print("\n🔍 Performing security audit...")
        audit_result = key_manager.get_key_security_audit()
        
        print("Security Audit Results:")
        print(f"  Total Keys: {audit_result['total_keys']}")
        print(f"  Active Keys: {audit_result['active_keys']}")
        print(f"  Expired Keys: {audit_result['expired_keys']}")
        print(f"  Old Keys: {audit_result['old_keys']}")
        print(f"  Keys Without Expiration: {audit_result['keys_without_expiration']}")
        print(f"  Encryption Enabled: {audit_result['encryption_enabled']}")
        print(f"  Auto Rotate Enabled: {audit_result['auto_rotate_enabled']}")
        
        if audit_result['security_recommendations']:
            print("\nSecurity Recommendations:")
            for rec in audit_result['security_recommendations']:
                print(f"  • {rec}")
        
        # 8. Test integration with settings module
        print("\n🔗 Testing integration with settings module...")
        
        # Store key using settings module
        settings_key_id = store_openrouter_api_key(
            "sk-or-settings-v1-integrationtest1234567890"
        )
        print(f"✅ Key stored via settings module: {settings_key_id}")
        
        # Retrieve key using settings module
        settings_key = get_openrouter_api_key()
        if settings_key:
            print(f"✅ Key retrieved via settings module: {settings_key[:20]}...")
        else:
            print("❌ Failed to retrieve key via settings module")
        
        # 9. Test cleanup of expired keys
        print("\n🧹 Testing cleanup of expired keys...")
        
        # Create an expired key for testing
        expired_key_id = key_manager.store_api_key(
            service="test",
            api_key="sk-test-expired",
            expires_in_days=-1  # Already expired
        )
        
        # Create an old inactive key
        old_key_id = key_manager.store_api_key(
            service="test",
            api_key="sk-test-old"
        )
        key_manager.revoke_api_key(old_key_id)
        
        # Manually set creation time to be old
        key_manager.api_keys[old_key_id].created_at = datetime.now() - timedelta(days=35)
        
        # Run cleanup
        cleaned_count = key_manager.cleanup_expired_keys()
        print(f"✅ Cleaned up {cleaned_count} expired/inactive keys")
        
        # 10. Test key format validation
        print("\n✅ Testing key format validation...")
        
        valid_keys = [
            ("sk-or-v1-1234567890abcdef", "openrouter"),
            ("sk-1234567890abcdef", "openai"),
            ("AIza1234567890abcdef", "google")
        ]
        
        invalid_keys = [
            ("invalid-key", "openrouter"),
            ("short", "openai"),
            ("", "google")
        ]
        
        print("Valid key formats:")
        for key, service in valid_keys:
            is_valid = key_manager.validate_api_key_format(key, service)
            status = "✅" if is_valid else "❌"
            print(f"  {status} {key[:20]}... ({service})")
        
        print("\nInvalid key formats:")
        for key, service in invalid_keys:
            is_valid = key_manager.validate_api_key_format(key, service)
            status = "✅" if is_valid else "❌"
            print(f"  {status} {key} ({service})")
        
        # 11. Export key information (without actual keys)
        print("\n📤 Exporting key information...")
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "keys": stored_keys,
            "audit": audit_result,
            "total_keys_managed": len(stored_keys)
        }
        
        export_file = f"api_key_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Key information exported to: {export_file}")
        
        print("\n🎯 API key encryption demonstration completed!")
        print("\n📚 Key Features Demonstrated:")
        print("  • Secure encryption of API keys")
        print("  • Password-protected key storage")
        print("  • Key rotation and revocation")
        print("  • Security auditing and recommendations")
        print("  • Integration with settings module")
        print("  • Key format validation")
        print("  • Automatic cleanup of expired keys")
        print("  • Export of key metadata")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Error in API key encryption example")
    
    finally:
        print("\n🛑 Cleaning up example keys...")
        # Clean up example keys
        try:
            for key_id in list(key_manager.api_keys.keys()):
                if "example" in key_manager.api_keys[key_id].metadata.get("created_by", ""):
                    key_manager.delete_api_key(key_id)
                    print(f"  Deleted example key: {key_id}")
        except Exception as e:
            print(f"  Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())