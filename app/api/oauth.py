"""
OAuth 2.0 API endpoints.
Implements OAuth 2.0 and OpenID Connect endpoints.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import JSONResponse, RedirectResponse
from app.auth.oauth_server import OAuth2AuthorizationServer
from app.core.jwt_manager import get_jwt_manager
from app.models.user import User
from app.auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "",
    state: str = None,
    code_challenge: str = None,
    code_challenge_method: str = None,
    nonce: str = None,
):
    """
    OAuth 2.0 Authorization Endpoint.
    
    Supports:
    - Authorization Code Flow (response_type=code)
    - PKCE (code_challenge, code_challenge_method)
    - OpenID Connect (scope includes 'openid', nonce)
    """
    # User must be authenticated
    user = await get_current_user(request)
    if not user:
        # Redirect to login with return URL
        return RedirectResponse(
            f"/login?redirect={request.url}",
            status_code=302
        )
    
    # Create authorization response
    oauth_server = request.app.state.oauth_server
    try:
        grant_user = user
        response = oauth_server.create_authorization_response(request, grant_user)
        return response
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token")
async def token(
    request: Request,
    grant_type: str = Form(...),
    code: str = Form(None),
    refresh_token: str = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(None),
    redirect_uri: str = Form(None),
    code_verifier: str = Form(None),
):
    """
    OAuth 2.0 Token Endpoint.
    
    Supported grant types:
    - authorization_code (with PKCE support)
    - refresh_token
    - client_credentials
    """
    oauth_server = request.app.state.oauth_server
    
    try:
        response = oauth_server.create_token_response(request)
        return response
    except Exception as e:
        logger.error(f"Token error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/userinfo")
async def userinfo(current_user: User = Depends(get_current_user)):
    """
    OpenID Connect UserInfo Endpoint.
    Returns user information based on access token scope.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get token scope from request
    # Return user info based on scope
    
    user_info = {
        "sub": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "picture": current_user.picture_url,
        "given_name": current_user.given_name,
        "family_name": current_user.family_name,
        "locale": current_user.locale or "en",
    }
    
    return JSONResponse(user_info)


@router.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    """
    OpenID Connect Discovery Endpoint.
    Provides metadata about the OpenID Provider.
    """
    base_url = str(request.base_url).rstrip('/')
    
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "userinfo_endpoint": f"{base_url}/oauth/userinfo",
        "jwks_uri": f"{base_url}/oauth/jwks.json",
        "response_types_supported": ["code", "token", "id_token", "code id_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email", "videos", "offline_access"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "claims_supported": ["sub", "name", "email", "email_verified", "given_name", "family_name", "picture", "locale"],
        "code_challenge_methods_supported": ["S256", "plain"],
    })


@router.get("/jwks.json")
async def jwks(request: Request):
    """
    JSON Web Key Set (JWKS) Endpoint.
    Provides public keys for token validation.
    """
    jwt_manager = get_jwt_manager()
    return JSONResponse(jwt_manager.get_jwks())


@router.post("/revoke")
async def revoke(
    request: Request,
    token: str = Form(...),
    token_type_hint: str = Form(None),
):
    """
    OAuth 2.0 Token Revocation Endpoint.
    Revokes access or refresh tokens.
    """
    jwt_manager = get_jwt_manager()
    
    try:
        jwt_manager.revoke_token(token)
        return JSONResponse({"message": "Token revoked"})
    except Exception as e:
        logger.error(f"Revocation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/introspect")
async def introspect(
    request: Request,
    token: str = Form(...),
):
    """
    OAuth 2.0 Token Introspection Endpoint.
    Returns metadata about a token.
    """
    jwt_manager = get_jwt_manager()
    
    payload = jwt_manager.validate_token(token)
    
    if not payload:
        return JSONResponse({
            "active": False
        })
    
    # Check if revoked
    if jwt_manager.is_token_revoked(token):
        return JSONResponse({
            "active": False
        })
    
    return JSONResponse({
        "active": True,
        "sub": payload.get("sub"),
        "scope": payload.get("scope"),
        "client_id": payload.get("client_id"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
    })
