import secrets
import hashlib
from typing import Tuple


def generate_invite_token() -> Tuple[str, str]:
    """
    Generate a secure invite token and its hash.
    
    Returns:
        Tuple of (plain_token, token_hash)
        - plain_token: The token to be sent to the invitee
        - token_hash: The hash to be stored in the database
    """
    plain_token = secrets.token_urlsafe(32)
    token_hash = hash_token(plain_token)
    return plain_token, token_hash


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256.
    
    Args:
        token: The plain text token
        
    Returns:
        The hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(plain_token: str, token_hash: str) -> bool:
    """
    Verify a plain token against its hash.
    
    Args:
        plain_token: The plain text token to verify
        token_hash: The stored hash to compare against
        
    Returns:
        True if the token matches, False otherwise
    """
    return hash_token(plain_token) == token_hash

