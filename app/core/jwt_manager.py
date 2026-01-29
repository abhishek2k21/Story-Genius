"""
JWT Token Manager.
Handles JWT token generation, validation, and key management.
"""
import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)


class JWTManager:
    """
    JWT Token Manager with RS256 signing.
    Uses asymmetric keys for enhanced security.
    """
    
    def __init__(self):
        """Initialize JWT manager with RSA keys."""
        self.private_key_path = os.getenv('JWT_PRIVATE_KEY_PATH', '/app/keys/jwt-private.pem')
        self.public_key_path = os.getenv('JWT_PUBLIC_KEY_PATH', '/app/keys/jwt-public.pem')
        
        # Load or generate keys
        self._load_or_generate_keys()
        
        # Token settings
        self.issuer = "https://api.ytvideocreator.com"
        self.access_token_expiry = timedelta(minutes=15)
        self.refresh_token_expiry = timedelta(days=30)
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        try:
            # Try to load existing keys
            with open(self.private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            
            with open(self.public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            
            logger.info("Loaded existing JWT keys")
        
        except FileNotFoundError:
            # Generate new keys
            logger.info("Generating new JWT keys...")
            self._generate_keys()
    
    def _generate_keys(self):
        """Generate new RSA key pair."""
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Get public key
        self.public_key = self.private_key.public_key()
        
        # Save keys to files
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
        
        # Save private key
        with open(self.private_key_path, 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(self.public_key_path, 'wb') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        logger.info("Generated and saved new JWT keys")
    
    def get_private_key(self) -> bytes:
        """Get private key in PEM format."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def get_public_key(self) -> bytes:
        """Get public key in PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def generate_access_token(
        self,
        user_id: str,
        scopes: list = None,
        additional_claims: dict = None
    ) -> str:
        """
        Generate JWT access token.
        
        Args:
            user_id: User identifier
            scopes: List of OAuth scopes
            additional_claims: Additional JWT claims
            
        Returns:
            JWT access token string
        """
        now = datetime.utcnow()
        
        payload = {
            'iss': self.issuer,
            'sub': str(user_id),
            'iat': int(now.timestamp()),
            'exp': int((now + self.access_token_expiry).timestamp()),
            'scope': ' '.join(scopes) if scopes else '',
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(
            payload,
            self.get_private_key(),
            algorithm='RS256'
        )
        
        return token
    
    def generate_refresh_token(self, user_id: str, client_id: str) -> str:
        """
        Generate JWT refresh token.
        
        Args:
            user_id: User identifier
            client_id: OAuth client ID
            
        Returns:
            JWT refresh token string
        """
        now = datetime.utcnow()
        
        payload = {
            'iss': self.issuer,
            'sub': str(user_id),
            'client_id': client_id,
            'iat': int(now.timestamp()),
            'exp': int((now + self.refresh_token_expiry).timestamp()),
            'type': 'refresh',
        }
        
        token = jwt.encode(
            payload,
            self.get_private_key(),
            algorithm='RS256'
        )
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.get_public_key(),
                algorithms=['RS256'],
                issuer=self.issuer
            )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def is_token_revoked(self, token: str) -> bool:
        """
        Check if token is revoked.
        
        Args:
            token: JWT token string
            
        Returns:
            True if revoked, False otherwise
        """
        # Check token revocation list (in Redis or database)
        # This is a simplified implementation
        from app.core.cache import get_redis_client
        
        redis = get_redis_client()
        jti = self.validate_token(token).get('jti') if self.validate_token(token) else None
        
        if jti:
            return redis.exists(f"revoked_token:{jti}")
        
        return False
    
    def revoke_token(self, token: str):
        """
        Revoke a token.
        
        Args:
            token: JWT token string
        """
        payload = self.validate_token(token)
        if not payload:
            return
        
        jti = payload.get('jti')
        exp = payload.get('exp')
        
        if jti and exp:
            from app.core.cache import get_redis_client
            redis = get_redis_client()
            
            # Store in revocation list until expiry
            ttl = exp - int(datetime.utcnow().timestamp())
            if ttl > 0:
                redis.setex(f"revoked_token:{jti}", ttl, "1")
                logger.info(f"Token {jti} revoked")
    
    def get_jwks(self) -> Dict:
        """
        Get JSON Web Key Set (JWKS) for token validation.
        Used by clients to validate tokens.
        
        Returns:
            JWKS dictionary
        """
        # Get public key in JWK format
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        public_numbers = self.public_key.public_numbers()
        
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": JWTManager._int_to_base64(public_numbers.n),
                    "e": JWTManager._int_to_base64(public_numbers.e),
                }
            ]
        }
    
    @staticmethod
    def _int_to_base64(value: int) -> str:
        """Convert integer to base64url."""
        import base64
        
        value_bytes = value.to_bytes((value.bit_length() + 7) // 8, 'big')
        return base64.urlsafe_b64encode(value_bytes).decode('utf-8').rstrip('=')


# Singleton instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get singleton JWT manager instance."""
    global _jwt_manager
    
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    
    return _jwt_manager
