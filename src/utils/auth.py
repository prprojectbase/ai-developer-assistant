"""
Authentication utilities for AI Developer Assistant
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import base64

from ..config.settings import get_settings


@dataclass
class AuthToken:
    """Authentication token structure"""
    token_id: str
    agent_id: str
    secret: str
    created_at: datetime
    expires_at: datetime
    permissions: list[str]


class AuthManager:
    """Authentication manager for agent communication"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tokens: Dict[str, AuthToken] = {}
        self.agent_secrets: Dict[str, str] = {}
        
        # Security settings
        self.token_lifetime = timedelta(hours=24)
        self.algorithm = "HS256"
        
    def generate_agent_secret(self, agent_id: str) -> str:
        """Generate a secret for an agent"""
        if agent_id in self.agent_secrets:
            return self.agent_secrets[agent_id]
        
        # Generate cryptographically secure random secret
        secret = secrets.token_urlsafe(32)
        self.agent_secrets[agent_id] = secret
        return secret
    
    def create_token(self, agent_id: str, permissions: list[str] = None) -> AuthToken:
        """Create an authentication token for an agent"""
        if permissions is None:
            permissions = ["read", "write", "execute"]
        
        # Generate token components
        token_id = secrets.token_urlsafe(16)
        secret = self.generate_agent_secret(agent_id)
        
        # Create token
        token = AuthToken(
            token_id=token_id,
            agent_id=agent_id,
            secret=secret,
            created_at=datetime.now(),
            expires_at=datetime.now() + self.token_lifetime,
            permissions=permissions
        )
        
        self.tokens[token_id] = token
        return token
    
    def validate_token(self, token_id: str, signature: str, message: str) -> Optional[AuthToken]:
        """Validate an authentication token"""
        if token_id not in self.tokens:
            return None
        
        token = self.tokens[token_id]
        
        # Check expiration
        if datetime.now() > token.expires_at:
            del self.tokens[token_id]
            return None
        
        # Verify signature
        expected_signature = self._sign_message(token.secret, message)
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        return token
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke an authentication token"""
        if token_id in self.tokens:
            del self.tokens[token_id]
            return True
        return False
    
    def revoke_agent_tokens(self, agent_id: str) -> int:
        """Revoke all tokens for an agent"""
        revoked_count = 0
        tokens_to_remove = []
        
        for token_id, token in self.tokens.items():
            if token.agent_id == agent_id:
                tokens_to_remove.append(token_id)
                revoked_count += 1
        
        for token_id in tokens_to_remove:
            del self.tokens[token_id]
        
        return revoked_count
    
    def _sign_message(self, secret: str, message: str) -> str:
        """Sign a message with HMAC"""
        return hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def create_signed_message(self, token_id: str, message_data: Dict) -> Dict:
        """Create a signed message for transmission"""
        if token_id not in self.tokens:
            raise ValueError("Invalid token ID")
        
        token = self.tokens[token_id]
        
        # Create message string
        message_str = json.dumps(message_data, sort_keys=True)
        
        # Sign message
        signature = self._sign_message(token.secret, message_str)
        
        # Create signed message
        signed_message = {
            "auth": {
                "token_id": token_id,
                "signature": signature,
                "timestamp": int(time.time()),
                "agent_id": token.agent_id
            },
            "data": message_data
        }
        
        return signed_message
    
    def verify_signed_message(self, signed_message: Dict) -> Tuple[bool, Optional[AuthToken], Optional[Dict]]:
        """Verify a signed message"""
        try:
            auth_data = signed_message.get("auth", {})
            message_data = signed_message.get("data", {})
            
            token_id = auth_data.get("token_id")
            signature = auth_data.get("signature")
            timestamp = auth_data.get("timestamp")
            
            if not all([token_id, signature, timestamp]):
                return False, None, None
            
            # Check timestamp (prevent replay attacks)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:  # 5 minute window
                return False, None, None
            
            # Create message string for verification
            message_str = json.dumps(message_data, sort_keys=True)
            
            # Validate token
            token = self.validate_token(token_id, signature, message_str)
            if token is None:
                return False, None, None
            
            return True, token, message_data
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return False, None, None
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        current_time = datetime.now()
        expired_tokens = []
        
        for token_id, token in self.tokens.items():
            if current_time > token.expires_at:
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            del self.tokens[token_id]
        
        return len(expired_tokens)
    
    def get_token_info(self, token_id: str) -> Optional[Dict]:
        """Get information about a token"""
        if token_id not in self.tokens:
            return None
        
        token = self.tokens[token_id]
        return {
            "token_id": token.token_id,
            "agent_id": token.agent_id,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "permissions": token.permissions,
            "is_expired": datetime.now() > token.expires_at
        }
    
    def list_agent_tokens(self, agent_id: str) -> list[Dict]:
        """List all tokens for an agent"""
        tokens = []
        for token_id, token in self.tokens.items():
            if token.agent_id == agent_id:
                tokens.append(self.get_token_info(token_id))
        return tokens


class WebSocketAuthMiddleware:
    """WebSocket authentication middleware"""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    async def authenticate_connection(self, websocket, path: str) -> Tuple[bool, Optional[AuthToken]]:
        """Authenticate a WebSocket connection"""
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get("type") != "auth":
                return False, None
            
            # Verify authentication
            is_valid, token, _ = self.auth_manager.verify_signed_message(auth_data)
            
            if not is_valid:
                return False, None
            
            return True, token
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return False, None
    
    async def send_auth_response(self, websocket, success: bool, token: Optional[AuthToken] = None):
        """Send authentication response"""
        response = {
            "type": "auth_response",
            "success": success
        }
        
        if success and token:
            response["token_info"] = self.auth_manager.get_token_info(token.token_id)
        
        await websocket.send(json.dumps(response))
    
    def wrap_message(self, token_id: str, message_data: Dict) -> Dict:
        """Wrap a message with authentication"""
        return self.auth_manager.create_signed_message(token_id, message_data)
    
    def unwrap_message(self, signed_message: Dict) -> Tuple[bool, Optional[AuthToken], Optional[Dict]]:
        """Unwrap and verify a signed message"""
        return self.auth_manager.verify_signed_message(signed_message)


# Global authentication manager instance
auth_manager = AuthManager()

# Add convenience methods for AgentClient
def sign_message(message_data: Dict, token_id: str) -> Dict:
    """Sign a message with the given token"""
    return auth_manager.create_signed_message(token_id, message_data)

def unwrap_message(signed_message: Dict) -> Tuple[bool, Optional[AuthToken], Optional[Dict]]:
    """Unwrap and verify a signed message"""
    return auth_manager.verify_signed_message(signed_message)