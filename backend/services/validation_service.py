import re
import html
from typing import Any, Optional, List
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_value: Any
    errors: List[str]
    warnings: List[str]

class ValidationService:
    def __init__(self):
        # Security patterns
        self.sql_injection_pattern = re.compile(
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)',
            re.IGNORECASE
        )
        self.xss_pattern = re.compile(
            r'<script[^>]*>.*?</script>|javascript:|on\w+\s*=',
            re.IGNORECASE
        )
        self.path_traversal_pattern = re.compile(
            r'\.\./|\.\.\\',
            re.IGNORECASE
        )
        self.command_injection_pattern = re.compile(
            r'[;&|`$()]',
            re.IGNORECASE
        )
        
        # Validation rules
        self.max_username_length = 50
        self.min_username_length = 3
        self.max_password_length = 100
        self.min_password_length = 4
        self.max_question_length = 2000
        self.min_question_length = 1
        self.max_filename_length = 255
        self.allowed_extensions = {'.pdf'}
    
    def validate_username(self, username: str) -> ValidationResult:
        """Validate username input."""
        errors = []
        warnings = []
        
        if not username:
            errors.append("Username is required")
            return ValidationResult(False, "", errors, warnings)
        
        # Length validation
        if len(username) < self.min_username_length:
            errors.append(f"Username must be at least {self.min_username_length} characters")
        if len(username) > self.max_username_length:
            errors.append(f"Username must not exceed {self.max_username_length} characters")
        
        # Character validation (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Security checks
        if self.sql_injection_pattern.search(username):
            errors.append("Username contains potentially dangerous characters")
        
        sanitized = username.strip()
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_password(self, password: str) -> ValidationResult:
        """Validate password input."""
        errors = []
        warnings = []
        
        if not password:
            errors.append("Password is required")
            return ValidationResult(False, "", errors, warnings)
        
        # Length validation
        if len(password) < self.min_password_length:
            errors.append(f"Password must be at least {self.min_password_length} characters")
        if len(password) > self.max_password_length:
            errors.append(f"Password must not exceed {self.max_password_length} characters")
        
        # Security warning (not blocking)
        if len(password) < 8:
            warnings.append("Password is weak. Consider using a longer passphrase.")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=password,  # Don't sanitize passwords
            errors=errors,
            warnings=warnings
        )
    
    def validate_question(self, question: str) -> ValidationResult:
        """Validate user question input."""
        errors = []
        warnings = []
        
        if not question or not question.strip():
            errors.append("Question is required")
            return ValidationResult(False, "", errors, warnings)
        
        # Length validation
        if len(question) < self.min_question_length:
            errors.append(f"Question must be at least {self.min_question_length} character")
        if len(question) > self.max_question_length:
            errors.append(f"Question must not exceed {self.max_question_length} characters")
        
        # Security checks
        if self.sql_injection_pattern.search(question):
            errors.append("Question contains potentially dangerous SQL patterns")
        
        if self.xss_pattern.search(question):
            errors.append("Question contains potentially dangerous script patterns")
        
        if self.command_injection_pattern.search(question):
            errors.append("Question contains potentially dangerous command patterns")
        
        # Sanitize the input
        sanitized = self.sanitize_html(question.strip())
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_filename(self, filename: str) -> ValidationResult:
        """Validate uploaded filename."""
        errors = []
        warnings = []
        
        if not filename:
            errors.append("Filename is required")
            return ValidationResult(False, "", errors, warnings)
        
        # Length validation
        if len(filename) > self.max_filename_length:
            errors.append(f"Filename must not exceed {self.max_filename_length} characters")
        
        # Extension validation
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext.lower() not in self.allowed_extensions:
            errors.append(f"Only {', '.join(self.allowed_extensions)} files are allowed")
        
        # Security checks
        if self.path_traversal_pattern.search(filename):
            errors.append("Filename contains path traversal patterns")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            errors.append("Filename contains invalid characters")
        
        # Sanitize filename
        sanitized = self.sanitize_filename(filename)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings
        )
    
    def validate_session_id(self, session_id: Optional[str]) -> ValidationResult:
        """Validate session ID."""
        errors = []
        warnings = []
        
        if not session_id:
            # Session ID is optional
            return ValidationResult(True, None, [], [])
        
        # Length validation
        if len(session_id) > 100:
            errors.append("Session ID is too long")
        
        # Character validation (UUID format typically)
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            errors.append("Session ID contains invalid characters")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=session_id.strip() if session_id else None,
            errors=errors,
            warnings=warnings
        )
    
    def sanitize_html(self, text: str) -> str:
        """Enhanced HTML sanitization to prevent XSS attacks."""
        # Escape HTML entities
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks."""
        # Remove path components
        sanitized = filename.replace('\\', '/').split('/')[-1]
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '', sanitized)
        # Strip leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        return sanitized
    
    def validate_json_payload(self, payload: dict, required_fields: List[str]) -> ValidationResult:
        """Validate JSON payload structure."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
            elif payload[field] is None or (isinstance(payload[field], str) and not payload[field].strip()):
                errors.append(f"Field '{field}' cannot be empty")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=payload,
            errors=errors,
            warnings=warnings
        )
    
    def check_rate_limit(self, user_id: int, endpoint: str, rate_limits: dict) -> bool:
        """
        Check if user has exceeded rate limits.
        This is a placeholder - actual implementation would use Redis or similar.
        """
        # Placeholder for rate limiting logic
        # In production, this would check against a Redis store
        return True

validation_service = ValidationService()