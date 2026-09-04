import os
import secrets
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("enterprise_agent")

class SecretsManager:
    """
    Enhanced secrets management service with validation and fallback strategies.
    Supports environment variables, file-based secrets, and secure defaults.
    """
    
    def __init__(self):
        load_dotenv()
        self.secrets_file = Path(".secrets")
        self.required_secrets = {
            "GROQ_API_KEY": {"required": True, "min_length": 20},
            "JWT_SECRET_KEY": {"required": True, "min_length": 32},
            "CORS_ALLOWED_ORIGINS": {"required": False, "min_length": 10},  # Made optional with default
        }
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Get a secret value with multiple fallback strategies.
        
        Priority order:
        1. Environment variable
        2. Secrets file (.secrets)
        3. Provided default
        4. Secure random generation (for certain secrets)
        """
        # Try environment variable first
        value = os.getenv(secret_name)
        if value:
            logger.info(f"Loaded {secret_name} from environment variable")
            return value
        
        # Try secrets file
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith(f"{secret_name}="):
                            value = line.split('=', 1)[1].strip()
                            logger.info(f"Loaded {secret_name} from secrets file")
                            return value
            except Exception as e:
                logger.warning(f"Failed to read secrets file: {e}")
        
        # Use default if provided
        if default is not None:
            logger.info(f"Using default value for {secret_name}")
            return default
        
        # Provide secure defaults for certain secrets
        if secret_name == "CORS_ALLOWED_ORIGINS":
            default_value = "http://localhost:8501"
            logger.info(f"Using default CORS_ALLOWED_ORIGINS: {default_value}")
            return default_value
        
        # Generate secure random for certain secrets
        if secret_name == "JWT_SECRET_KEY":
            generated = self._generate_secure_secret(32)
            logger.warning(f"Generated random JWT_SECRET_KEY. Set this in your environment for production.")
            return generated
        
        # Return empty string if no value found
        logger.error(f"Secret {secret_name} not found and no default provided")
        return ""
    
    def validate_secrets(self) -> dict:
        """
        Validate that all required secrets are present and meet requirements.
        Returns a dictionary with validation results.
        """
        validation_results = {
            "valid": True,
            "missing_secrets": [],
            "invalid_secrets": [],
            "warnings": []
        }
        
        for secret_name, requirements in self.required_secrets.items():
            value = self.get_secret(secret_name)
            
            if not value and requirements.get("required", False):
                validation_results["valid"] = False
                validation_results["missing_secrets"].append(secret_name)
                continue
            
            if value and len(value) < requirements.get("min_length", 0):
                validation_results["valid"] = False
                validation_results["invalid_secrets"].append(
                    f"{secret_name} (minimum length: {requirements['min_length']})"
                )
        
        # Additional checks
        if not self.get_secret("GROQ_API_KEY").startswith("gsk_"):
            validation_results["warnings"].append("GROQ_API_KEY should start with 'gsk_'")
        
        if self.get_secret("JWT_SECRET_KEY") == "generate-a-long-random-secret":
            validation_results["warnings"].append("JWT_SECRET_KEY is using default value. Generate a secure secret for production.")
        
        return validation_results
    
    def _generate_secure_secret(self, length: int = 32) -> str:
        """Generate a cryptographically secure random secret."""
        return secrets.token_urlsafe(length)
    
    def set_secret(self, secret_name: str, value: str) -> bool:
        """
        Store a secret in the secrets file.
        Returns True if successful, False otherwise.
        """
        try:
            # Create secrets file if it doesn't exist
            if not self.secrets_file.exists():
                self.secrets_file.touch(mode=0o600)
            
            # Read existing secrets
            existing_secrets = {}
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, val = line.split('=', 1)
                            existing_secrets[key.strip()] = val.strip()
            
            # Update with new secret
            existing_secrets[secret_name] = value
            
            # Write back to file
            with open(self.secrets_file, 'w') as f:
                for key, val in existing_secrets.items():
                    f.write(f"{key}={val}\n")
            
            logger.info(f"Secret {secret_name} stored in secrets file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret {secret_name}: {e}")
            return False
    
    def get_database_url(self) -> str:
        """
        Get database URL with proper validation.
        Returns SQLite path by default, PostgreSQL URL if configured.
        """
        postgres_url = os.getenv("DATABASE_URL", "").strip()
        if postgres_url:
            # Validate PostgreSQL URL format
            if not postgres_url.startswith("postgresql://"):
                logger.warning("DATABASE_URL doesn't start with postgresql://, using SQLite instead")
                return ""
            return postgres_url
        
        # Default to SQLite
        sqlite_path = os.getenv("DATABASE_PATH", "").strip()
        if not sqlite_path:
            sqlite_path = "backend/data/enterprise.db"
        
        return sqlite_path
    
    def setup_production_secrets(self) -> dict:
        """
        Setup production-ready secrets with validation.
        Returns setup results.
        """
        results = {
            "success": True,
            "actions_taken": [],
            "warnings": []
        }
        
        # Validate current secrets
        validation = self.validate_secrets()
        
        if not validation["valid"]:
            results["success"] = False
            results["actions_taken"].append(f"Missing secrets: {', '.join(validation['missing_secrets'])}")
            
            # Generate missing secrets where possible
            for secret_name in validation["missing_secrets"]:
                if secret_name == "JWT_SECRET_KEY":
                    generated = self._generate_secure_secret(32)
                    self.set_secret(secret_name, generated)
                    results["actions_taken"].append(f"Generated {secret_name}")
        
        if validation["warnings"]:
            results["warnings"] = validation["warnings"]
        
        return results

# Global secrets manager instance
secrets_manager = SecretsManager()