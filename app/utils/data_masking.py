"""
PII Data Masking Utilities.
Masks sensitive data in logs to prevent PII exposure.
"""
import re
from typing import Optional


def mask_email(email: str) -> str:
    """
    Mask email for logs.
    
    Example: user@example.com → u***@example.com
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 1:
        return f"{local}***@{domain}"
    
    return f"{local[0]}***@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number.
    
    Example: +1234567890 → +123***7890
    """
    if not phone or len(phone) < 8:
        return "***"
    
    return f"{phone[:4]}***{phone[-4:]}"


def mask_credit_card(cc: str) -> str:
    """
    Mask credit card number.
    
    Example: 1234567890123456 → ************3456
    """
    if not cc or len(cc) < 4:
        return "****"
    
    return f"{'*' * (len(cc) - 4)}{cc[-4:]}"


def mask_ssn(ssn: str) -> str:
    """
    Mask SSN.
    
    Example: 123-45-6789 → ***-**-6789
    """
    if not ssn or len(ssn) < 4:
        return "***"
    
    # Keep last 4 digits
    return f"***-**-{ssn[-4:]}"


def mask_ip_address(ip: str) -> str:
    """
    Mask IP address (partial anonymization).
    
    Example: 192.168.1.100 → 192.168.x.x
    """
    if not ip:
        return ip
    
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.x.x"
    
    # IPv6
    if ':' in ip:
        parts = ip.split(':')
        if len(parts) >= 4:
            return f"{parts[0]}:{parts[1]}:****:****"
    
    return "x.x.x.x"


def mask_api_key(key: str) -> str:
    """
    Mask API key.
    
    Example: sk_live_abcdefghijklmnop → sk_live_abc***nop
    """
    if not key or len(key) < 10:
        return "***"
    
    return f"{key[:8]}***{key[-3:]}"


def mask_jwt_token(token: str) -> str:
    """
    Mask JWT token.
    
    Example: eyJhbGciOiJIUzI1NiIsInR5... → eyJh***
    """
    if not token or len(token) < 20:
        return "***"
    
    return f"{token[:10]}***"


def mask_password(password: str) -> str:
    """Completely mask password."""
    return "********"


def mask_pii_in_text(text: str) -> str:
    """
    Automatically detect and mask PII in text.
    
    Detects:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - SSNs
    """
    if not text:
        return text
    
    # Mask emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, lambda m: mask_email(m.group()), text)
    
    # Mask credit cards (16 digits)
    cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    text = re.sub(cc_pattern, lambda m: mask_credit_card(m.group().replace(' ', '').replace('-', '')), text)
    
    # Mask SSN
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    text = re.sub(ssn_pattern, lambda m: mask_ssn(m.group()), text)
    
    # Mask phone numbers
    phone_pattern = r'\+?\d{1,3}[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b'
    text = re.sub(phone_pattern, lambda m: mask_phone(m.group()), text)
    
    return text


def mask_dict_pii(data: dict, sensitive_keys: list = None) -> dict:
    """
    Mask PII in dictionary (for logging).
    
    Args:
        data: Dictionary to mask
        sensitive_keys: List of keys that contain PII
        
    Returns:
        Dictionary with masked values
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'email', 'phone', 'ssn', 'credit_card', 'password',
            'api_key', 'token', 'secret', 'ip_address'
        ]
    
    masked = {}
    
    for key, value in data.items():
        if any(sk in key.lower() for sk in sensitive_keys):
            # Mask based on key type
            if 'email' in key.lower():
                masked[key] = mask_email(str(value))
            elif 'phone' in key.lower():
                masked[key] = mask_phone(str(value))
            elif 'credit' in key.lower() or 'card' in key.lower():
                masked[key] = mask_credit_card(str(value))
            elif 'ssn' in key.lower():
                masked[key] = mask_ssn(str(value))
            elif 'password' in key.lower() or 'secret' in key.lower():
                masked[key] = mask_password(str(value))
            elif 'token' in key.lower() or 'key' in key.lower():
                masked[key] = mask_api_key(str(value))
            elif 'ip' in key.lower():
                masked[key] = mask_ip_address(str(value))
            else:
                masked[key] = "***"
        else:
            masked[key] = value
    
    return masked


# Example usage in logging
class PIIMaskingFormatter(logging.Formatter):
    """Custom logging formatter that masks PII."""
    
    def format(self, record):
        # Mask PII in message
        if hasattr(record, 'msg'):
            record.msg = mask_pii_in_text(str(record.msg))
        
        return super().format(record)


if __name__ == "__main__":
    # Test masking functions
    print(mask_email("john.doe@example.com"))  # j***@example.com
    print(mask_phone("+1234567890"))  # +123***7890
    print(mask_credit_card("1234567890123456"))  # ************3456
    print(mask_ssn("123-45-6789"))  # ***-**-6789
    print(mask_ip_address("192.168.1.100"))  # 192.168.x.x
    
    text = "User email is john@example.com, phone +1234567890, SSN 123-45-6789"
    print(mask_pii_in_text(text))
