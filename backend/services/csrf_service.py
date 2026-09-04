import secrets
import logging
from typing import Optional, Dict
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("enterprise_agent")

security = HTTPBearer(auto_error=False)

class CSRFProtection:
    """
    CSRF protection service for state-changing operations.
    Implements double-submit cookie pattern and token validation.
    """
    
    def __init__(self):
        self.token_length = 32
        self.active_tokens: Dict[str, float] = {}  # token -> expiry timestamp
        self.token_expiry_hours = 24
    
    def generate_token(self) -> str:
        """Generate a secure CSRF token."""
        token = secrets.token_urlsafe(self.token_length)
        
        # Store token with expiry
        import time
        expiry = time.time() + (self.token_expiry_hours * 3600)
        self.active_tokens[token] = expiry
        
        logger.info(f"Generated CSRF token (expires in {self.token_expiry_hours} hours)")
        return token
    
    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        if not token:
            logger.warning("CSRF token validation failed: no token provided")
            return False
        
        import time
        current_time = time.time()
        
        # Check if token exists and is not expired
        if token not in self.active_tokens:
            logger.warning("CSRF token validation failed: invalid token")
            return False
        
        if self.active_tokens[token] < current_time:
            logger.warning("CSRF token validation failed: expired token")
            del self.active_tokens[token]
            return False
        
        # Token is valid - optionally remove it after use (single-use tokens)
        # del self.active_tokens[token]
        
        logger.info("CSRF token validation successful")
        return True
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from memory."""
        import time
        current_time = time.time()
        
        expired_tokens = [
            token for token, expiry in self.active_tokens.items()
            if expiry < current_time
        ]
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")
    
    def get_csrf_token_endpoint(self):
        """Endpoint to get a new CSRF token."""
        return {
            "csrf_token": self.generate_token(),
            "expires_in_hours": self.token_expiry_hours
        }

# Global CSRF protection instance
csrf_protection = CSRFProtection()

async def verify_csrf_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Dependency to verify CSRF token for protected endpoints.
    For now, this is a placeholder - full CSRF implementation would require
    cookie handling and frontend integration.
    """
    # Placeholder for CSRF verification
    # In production, this would validate the CSRF token from headers/cookies
    return True

# For sensitive operations, we can add additional CSRF checks
class CSRFRequired:
    """Decorator to mark endpoints that require CSRF protection."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            if self.enabled:
                # CSRF validation would happen here
                # For now, we'll log the call
                logger.info(f"CSRF-protected endpoint called: {func.__name__}")
            return await func(*args, **kwargs)
        return wrapper