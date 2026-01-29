"""
Vault client for Python applications.
Automatically authenticates using Kubernetes service account.
"""
import hvac
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class VaultClient:
    """
    HashiCorp Vault client with automatic Kubernetes authentication.
    """
    
    def __init__(
        self,
        vault_addr: str = None,
        role: str = "app-backend",
        jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ):
        """
        Initialize Vault client.
        
        Args:
            vault_addr: Vault server address (defaults to VAULT_ADDR env var)
            role: Kubernetes auth role name
            jwt_path: Path to service account JWT token
        """
        self.vault_addr = vault_addr or os.getenv('VAULT_ADDR', 'http://vault.vault:8200')
        self.role = role
        self.jwt_path = jwt_path
        
        self.client = hvac.Client(url=self.vault_addr)
        self._authenticate()
        
        logger.info(f"VaultClient initialized (addr={self.vault_addr}, role={role})")
    
    def _authenticate(self):
        """Authenticate with Vault using Kubernetes service account."""
        try:
            # Read JWT token
            with open(self.jwt_path, 'r') as f:
                jwt = f.read().strip()
            
            # Authenticate
            response = self.client.auth.kubernetes.login(
                role=self.role,
                jwt=jwt
            )
            
            # Extract token
            self.client.token = response['auth']['client_token']
            
            logger.info("✅ Successfully authenticated with Vault")
        
        except FileNotFoundError:
            logger.warning(f"JWT token not found at {self.jwt_path}. Running outside Kubernetes?")
            # In local development, use token from environment
            token = os.getenv('VAULT_TOKEN')
            if token:
                self.client.token = token
                logger.info("Using VAULT_TOKEN from environment")
            else:
                raise ValueError("Cannot authenticate with Vault")
        
        except Exception as e:
            logger.error(f"Failed to authenticate with Vault: {e}")
            raise
    
    def get_secret(self, path: str, mount_point: str = "secret") -> Dict[str, Any]:
        """
        Get secret from Vault KV v2 engine.
        
        Args:
            path: Secret path (e.g., 'app-backend/config')
            mount_point: KV mount point (default: 'secret')
            
        Returns:
            Dictionary of secret data
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            return response['data']['data']
        
        except Exception as e:
            logger.error(f"Failed to read secret '{path}': {e}")
            raise
    
    def set_secret(
        self,
        path: str,
        secrets: Dict[str, Any],
        mount_point: str = "secret"
    ):
        """
        Write secret to Vault KV v2 engine.
        
        Args:
            path: Secret path (e.g., 'app-backend/config')
            secrets: Dictionary of secret key-value pairs
            mount_point: KV mount point (default: 'secret')
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secrets,
                mount_point=mount_point
            )
            logger.info(f"✅ Secret written to '{path}'")
        
        except Exception as e:
            logger.error(f"Failed to write secret '{path}': {e}")
            raise
    
    def get_database_credentials(self, role: str = "app-backend") -> Dict[str, str]:
        """
        Get dynamic database credentials.
        
        Args:
            role: Database role name
            
        Returns:
            Dictionary with 'username' and 'password'
        """
        try:
            response = self.client.secrets.database.generate_credentials(
                name=role
            )
            return {
                'username': response['data']['username'],
                'password': response['data']['password'],
                'lease_id': response['lease_id'],
                'lease_duration': response['lease_duration']
            }
        
        except Exception as e:
            logger.error(f"Failed to get database credentials: {e}")
            raise
    
    def renew_token(self):
        """Renew Vault token before it expires."""
        try:
            self.client.auth.token.renew_self()
            logger.info("✅ Vault token renewed")
        except Exception as e:
            logger.warning(f"Failed to renew token, re-authenticating: {e}")
            self._authenticate()
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        try:
            return self.client.is_authenticated()
        except:
            return False


# Singleton instance
_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    """
    Get singleton Vault client instance.
    
    Returns:
        VaultClient instance
    """
    global _vault_client
    
    if _vault_client is None:
        _vault_client = VaultClient()
    
    return _vault_client


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize client
    vault = get_vault_client()
    
    # Get secrets
    secrets = vault.get_secret("app-backend/config")
    print(f"Database URL: {secrets.get('database_url')}")
    
    # Get dynamic database credentials
    db_creds = vault.get_database_credentials("app-backend")
    print(f"Dynamic username: {db_creds['username']}")
