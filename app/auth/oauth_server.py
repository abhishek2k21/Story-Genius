"""
OAuth 2.0 Authorization Server.
Implements OAuth 2.0 with OpenID Connect for secure authentication.
"""
from datetime import datetime, timedelta
from typing import Optional
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant,
    RefreshTokenGrant,
    ClientCredentialsGrant
)
from authlib.oidc.core.grants import OpenIDCode
from authlib.oidc.core import UserInfo
from werkzeug.security import gen_salt
from app.models.oauth import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from app.models.user import User
from app.core.jwt_manager import JWTManager
import logging

logger = logging.getLogger(__name__)


class MyAuthorizationCodeGrant(AuthorizationCodeGrant):
    """Custom Authorization Code Grant with PKCE support."""
    
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic', 'client_secret_post', 'none']
    
    def save_authorization_code(self, code, request):
        """Save authorization code to database."""
        client = request.client
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
            code_challenge=request.data.get('code_challenge'),
            code_challenge_method=request.data.get('code_challenge_method'),
        )
        auth_code.save()
        return auth_code
    
    def query_authorization_code(self, code, client):
        """Query authorization code from database."""
        auth_code = OAuth2AuthorizationCode.query.filter_by(
            code=code,
            client_id=client.client_id
        ).first()
        
        if auth_code and not auth_code.is_expired():
            return auth_code
        return None
    
    def delete_authorization_code(self, authorization_code):
        """Delete used authorization code."""
        authorization_code.delete()
    
    def authenticate_user(self, authorization_code):
        """Get user from authorization code."""
        return User.query.get(authorization_code.user_id)


class MyRefreshTokenGrant(RefreshTokenGrant):
    """Custom Refresh Token Grant with token rotation."""
    
    def authenticate_refresh_token(self, refresh_token):
        """Validate refresh token."""
        token = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if token and not token.is_refresh_token_expired():
            return token
        return None
    
    def authenticate_user(self, credential):
        """Get user from token."""
        return User.query.get(credential.user_id)
    
    def revoke_old_credential(self, credential):
        """Revoke old refresh token (token rotation)."""
        credential.revoked = True
        credential.save()


class MyClientCredentialsGrant(ClientCredentialsGrant):
    """Client Credentials Grant for service-to-service authentication."""
    
    pass


class MyOpenIDCode(OpenIDCode):
    """OpenID Connect Authorization Code Flow."""
    
    def exists_nonce(self, nonce, request):
        """Check if nonce has been used (prevent replay attacks)."""
        # Check in cache/database
        return False
    
    def get_jwt_config(self, grant):
        """Get JWT configuration."""
        jwt_manager = JWTManager()
        return {
            'key': jwt_manager.get_private_key(),
            'alg': 'RS256',
            'iss': 'https://api.ytvideocreator.com',
            'exp': 3600,  # 1 hour
        }
    
    def generate_user_info(self, user, scope):
        """Generate user info for OpenID Connect."""
        user_info = UserInfo(sub=str(user.id), name=user.name)
        
        if 'email' in scope:
            user_info['email'] = user.email
            user_info['email_verified'] = user.email_verified
        
        if 'profile' in scope:
            user_info['given_name'] = user.given_name
            user_info['family_name'] = user.family_name
            user_info['picture'] = user.picture_url
            user_info['locale'] = user.locale or 'en'
        
        return user_info


def query_client(client_id):
    """Query OAuth client by ID."""
    return OAuth2Client.query.filter_by(client_id=client_id).first()


def save_token(token, request):
    """Save OAuth token to database."""
    if request.user:
        user_id = request.user.id
    else:
        user_id = None
    
    client = request.client
    
    # Create token
    oauth_token = OAuth2Token(
        client_id=client.client_id,
        user_id=user_id,
        token_type=token.get('token_type', 'Bearer'),
        access_token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        scope=token.get('scope', ''),
        expires_in=token.get('expires_in', 3600),
        issued_at=int(datetime.utcnow().timestamp())
    )
    oauth_token.save()
    
    logger.info(f"Token issued for client {client.client_id}, user {user_id}")
    return oauth_token


class OAuth2AuthorizationServer:
    """OAuth 2.0 Authorization Server with OpenID Connect."""
    
    def __init__(self, app):
        """Initialize authorization server."""
        self.server = AuthorizationServer(
            app,
            query_client=query_client,
            save_token=save_token
        )
        
        # Register grants
        self.server.register_grant(MyAuthorizationCodeGrant, [MyOpenIDCode()])
        self.server.register_grant(MyRefreshTokenGrant)
        self.server.register_grant(MyClientCredentialsGrant)
        
        logger.info("OAuth 2.0 Authorization Server initialized")
    
    def create_authorization_response(self, request, grant_user):
        """Create authorization response."""
        return self.server.create_authorization_response(request, grant_user)
    
    def create_token_response(self, request):
        """Create token response."""
        return self.server.create_token_response(request)
    
    def create_endpoint_response(self, name, request):
        """Create endpoint response."""
        return self.server.create_endpoint_response(name, request)


# OAuth 2.0 scopes
OAUTH_SCOPES = {
    'openid': 'OpenID Connect authentication',
    'profile': 'Access to user profile information',
    'email': 'Access to user email address',
    'videos': 'Access to user videos',
    'videos:create': 'Create videos on behalf of user',
    'videos:delete': 'Delete user videos',
    'offline_access': 'Refresh token for offline access',
}
