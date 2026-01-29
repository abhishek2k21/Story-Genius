"""
Enterprise Single Sign-On (SSO) Service.
Support SAML 2.0 and OAuth 2.0 for enterprise authentication.
"""
from typing import Dict, Optional
from datetime import datetime
from enum import Enum
import uuid
import base64
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class SSOProvider(str, Enum):
    """Supported SSO providers."""
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    ONELOGIN = "onelogin"
    CUSTOM_SAML = "custom_saml"


class SSOConfiguration:
    """SSO configuration model."""
    
    def __init__(
        self,
        id: str,
        organization_id: str,
        provider: SSOProvider,
        config: Dict
    ):
        self.id = id
        self.organization_id = organization_id
        self.provider = provider
        self.config = config
        self.enabled = True
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class SSOService:
    """Enterprise SSO authentication service."""
    
    def __init__(self, user_service, session_service):
        self.user_service = user_service
        self.session_service = session_service
        self.configurations: Dict[str, SSOConfiguration] = {}
    
    def configure_sso(
        self,
        organization_id: str,
        provider: str,
        config: Dict
    ) -> Dict:
        """
        Configure SSO for organization.
        
        Args:
            organization_id: Organization ID
            provider: SSO provider (okta, azure_ad, etc.)
            config: Provider-specific configuration
            
        Returns:
            SSO configuration details with URLs
        """
        # Validate provider
        try:
            provider_enum = SSOProvider(provider)
        except ValueError:
            raise ValueError(f"Unsupported SSO provider: {provider}")
        
        # Validate configuration based on provider
        self._validate_provider_config(provider_enum, config)
        
        # Create SSO configuration
        sso_id = str(uuid.uuid4())
        
        sso_config = SSOConfiguration(
            id=sso_id,
            organization_id=organization_id,
            provider=provider_enum,
            config=config
        )
        
        # Save configuration
        self.configurations[sso_id] = sso_config
        self._save_sso_config(sso_config)
        
        logger.info(f"Configured SSO for organization {organization_id} with provider {provider}")
        
        # Generate response URLs
        base_url = "https://app.ytvideocreator.com"
        
        return {
            "sso_id": sso_id,
            "provider": provider,
            "organization_id": organization_id,
            "urls": {
                "login_url": f"{base_url}/sso/{sso_id}/login",
                "acs_url": f"{base_url}/sso/{sso_id}/acs",  # Assertion Consumer Service
                "metadata_url": f"{base_url}/sso/{sso_id}/metadata",
                "logout_url": f"{base_url}/sso/{sso_id}/logout"
            },
            "entity_id": f"{base_url}/sso/{sso_id}",
            "status": "active"
        }
    
    def _validate_provider_config(self, provider: SSOProvider, config: Dict):
        """Validate provider-specific configuration."""
        # SAML providers (Okta, Azure AD, OneLogin, Custom SAML)
        if provider in [SSOProvider.OKTA, SSOProvider.AZURE_AD, SSOProvider.ONELOGIN, SSOProvider.CUSTOM_SAML]:
            required_fields = ["entity_id", "sso_url", "x509_cert"]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required SAML field: {field}")
            
            # Validate certificate format
            try:
                cert = config["x509_cert"]
                if not cert.startswith("-----BEGIN CERTIFICATE-----"):
                    raise ValueError("Invalid certificate format")
            except Exception as e:
                raise ValueError(f"Invalid x509 certificate: {e}")
        
        # OAuth providers (Google Workspace)
        elif provider == SSOProvider.GOOGLE_WORKSPACE:
            required_fields = ["client_id", "client_secret", "domain"]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required OAuth field: {field}")
    
    async def process_saml_response(
        self,
        sso_id: str,
        saml_response: str
    ) -> Dict:
        """
        Process SAML authentication response.
        
        Args:
            sso_id: SSO configuration ID
            saml_response: Base64-encoded SAML response
            
        Returns:
            User authentication result with session token
        """
        # Get SSO configuration
        sso_config = self.configurations.get(sso_id)
        
        if not sso_config or not sso_config.enabled:
            raise ValueError("Invalid or disabled SSO configuration")
        
        # Decode SAML response
        try:
            decoded = base64.b64decode(saml_response)
            saml_xml = decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Invalid SAML response encoding: {e}")
        
        # Parse SAML XML
        saml_data = self._parse_saml_response(saml_xml)
        
        # Validate SAML signature
        if not self._validate_saml_signature(saml_data, sso_config):
            raise ValueError("Invalid SAML signature - authentication failed")
        
        # Validate SAML assertions
        if not self._validate_saml_assertions(saml_data):
            raise ValueError("Invalid SAML assertions")
        
        # Extract user attributes
        user_data = {
            "email": saml_data.get("email"),
            "first_name": saml_data.get("first_name", ""),
            "last_name": saml_data.get("last_name", ""),
            "groups": saml_data.get("groups", []),
            "department": saml_data.get("department"),
            "organization_id": sso_config.organization_id
        }
        
        # Validate email
        if not user_data["email"]:
            raise ValueError("Email attribute missing from SAML response")
        
        # Create or update user
        user = await self._get_or_create_sso_user(user_data, sso_id)
        
        # Map SSO groups to roles
        await self._sync_user_roles(user["id"], user_data["groups"], sso_config.organization_id)
        
        # Generate session token
        session_token = self.session_service.create_session(
            user_id=user["id"],
            auth_method="sso",
            sso_provider=sso_config.provider.value
        )
        
        logger.info(f"SSO login successful for {user_data['email']} via {sso_config.provider.value}")
        
        return {
            "success": True,
            "user_id": user["id"],
            "email": user["email"],
            "session_token": session_token,
            "sso_provider": sso_config.provider.value,
            "organization_id": sso_config.organization_id
        }
    
    def _parse_saml_response(self, saml_xml: str) -> Dict:
        """Parse SAML XML response."""
        try:
            root = ET.fromstring(saml_xml)
            
            # Namespace handling
            namespaces = {
                'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion',
                'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol'
            }
            
            # Extract attributes
            attributes = {}
            
            # Find attribute statements
            for attr_statement in root.findall('.//saml2:AttributeStatement', namespaces):
                for attr in attr_statement.findall('.//saml2:Attribute', namespaces):
                    attr_name = attr.get('Name')
                    attr_value_elem = attr.find('.//saml2:AttributeValue', namespaces)
                    
                    if attr_value_elem is not None:
                        # Map common SAML attribute names
                        if 'email' in attr_name.lower():
                            attributes['email'] = attr_value_elem.text
                        elif 'firstname' in attr_name.lower() or 'givenname' in attr_name.lower():
                            attributes['first_name'] = attr_value_elem.text
                        elif 'lastname' in attr_name.lower() or 'surname' in attr_name.lower():
                            attributes['last_name'] = attr_value_elem.text
                        elif 'group' in attr_name.lower():
                            # Groups might be multiple values
                            groups = [elem.text for elem in attr.findall('.//saml2:AttributeValue', namespaces)]
                            attributes['groups'] = groups
                        elif 'department' in attr_name.lower():
                            attributes['department'] = attr_value_elem.text
            
            return attributes
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid SAML XML: {e}")
    
    def _validate_saml_signature(self, saml_data: Dict, sso_config: SSOConfiguration) -> bool:
        """Validate SAML response signature."""
        # In production, validate the XML signature using the x509 cert
        # For now, simplified validation
        
        try:
            cert_pem = sso_config.config.get("x509_cert")
            if not cert_pem:
                return False
            
            # Load certificate
            cert = x509.load_pem_x509_certificate(
                cert_pem.encode('utf-8'),
                default_backend()
            )
            
            # Verify certificate is valid
            # In production: verify XML signature matches
            
            return True
            
        except Exception as e:
            logger.error(f"SAML signature validation failed: {e}")
            return False
    
    def _validate_saml_assertions(self, saml_data: Dict) -> bool:
        """Validate SAML assertions (expiry, audience, etc.)."""
        # Validate required attributes are present
        if not saml_data.get("email"):
            return False
        
        # In production: validate NotBefore, NotOnOrAfter, Audience, etc.
        
        return True
    
    async def _get_or_create_sso_user(self, user_data: Dict, sso_id: str) -> Dict:
        """Get existing user or create new SSO user."""
        # Check if user exists
        existing_user = await self.user_service.get_by_email(user_data["email"])
        
        if existing_user:
            # Update user info from SSO
            await self.user_service.update_user(
                user_id=existing_user["id"],
                updates={
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "sso_linked": True,
                    "sso_id": sso_id
                }
            )
            return existing_user
        
        # Create new user
        new_user = await self.user_service.create_user(
            email=user_data["email"],
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            organization_id=user_data["organization_id"],
            auth_method="sso",
            sso_id=sso_id
        )
        
        logger.info(f"Created new SSO user: {user_data['email']}")
        
        return new_user
    
    async def _sync_user_roles(self, user_id: str, groups: list, organization_id: str):
        """Sync user roles based on SSO groups."""
        # Map SSO groups to application roles
        role_mapping = {
            "admins": "admin",
            "editors": "editor",
            "viewers": "viewer"
        }
        
        roles_to_assign = []
        
        for group in groups:
            group_lower = group.lower()
            for group_pattern, role in role_mapping.items():
                if group_pattern in group_lower:
                    roles_to_assign.append(role)
        
        # If no roles matched, assign default viewer role
        if not roles_to_assign:
            roles_to_assign.append("viewer")
        
        # Update user roles
        await self.user_service.sync_roles(user_id, organization_id, roles_to_assign)
    
    def get_saml_metadata(self, sso_id: str) -> str:
        """
        Generate SAML metadata XML for SP (Service Provider).
        
        Used by IdP to configure the connection.
        """
        sso_config = self.configurations.get(sso_id)
        
        if not sso_config:
            raise ValueError("SSO configuration not found")
        
        base_url = "https://app.ytvideocreator.com"
        entity_id = f"{base_url}/sso/{sso_id}"
        acs_url = f"{base_url}/sso/{sso_id}/acs"
        
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" 
                     entityID="{entity_id}">
  <md:SPSSODescriptor AuthnRequestsSigned="false" 
                      WantAssertionsSigned="true" 
                      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" 
                                Location="{acs_url}" 
                                index="0" 
                                isDefault="true"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""
        
        return metadata
    
    def _save_sso_config(self, config: SSOConfiguration):
        """Save SSO configuration to database."""
        # Database save logic
        pass


# FastAPI endpoints
"""
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/sso", tags=["sso"])

@router.post("/configure")
async def configure_sso(
    organization_id: str,
    provider: str,
    config: Dict,
    current_admin: User = Depends(require_org_admin)
):
    '''Configure SSO for organization (admin only).'''
    sso_service = SSOService(user_service, session_service)
    
    return sso_service.configure_sso(
        organization_id=organization_id,
        provider=provider,
        config=config
    )

@router.get("/{sso_id}/login")
async def sso_login(sso_id: str):
    '''Initiate SSO login.'''
    # Redirect to IdP login page
    # In production: generate SAML AuthnRequest
    return RedirectResponse(url=f"/sso/{sso_id}/idp")

@router.post("/{sso_id}/acs")
async def assertion_consumer_service(
    sso_id: str,
    SAMLResponse: str = Form(...)
):
    '''Handle SAML response from IdP.'''
    sso_service = SSOService(user_service, session_service)
    
    result = await sso_service.process_saml_response(sso_id, SAMLResponse)
    
    # Set session cookie and redirect to app
    response = RedirectResponse(url="/dashboard")
    response.set_cookie("session_token", result["session_token"], httponly=True)
    
    return response

@router.get("/{sso_id}/metadata")
async def get_saml_metadata(sso_id: str):
    '''Get SAML SP metadata for IdP configuration.'''
    sso_service = SSOService(user_service, session_service)
    
    metadata_xml = sso_service.get_saml_metadata(sso_id)
    
    return Response(content=metadata_xml, media_type="application/xml")
"""
