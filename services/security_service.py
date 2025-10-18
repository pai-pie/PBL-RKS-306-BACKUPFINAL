import hashlib
import secrets
import re

class SecurityService:
    def __init__(self):
        # Tidak perlu bcrypt, pakai built-in hashlib
        print("🔒 Using built-in hashing (no bcrypt)")
    
    def hash_password(self, password):
        """Hash password dengan SHA-256 + salt"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate random salt
        salt = secrets.token_hex(16)
        # Hash password + salt
        hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        # Format: algorithm$salt$hash
        return f"sha256${salt}${hashed}"
    
    def verify_password(self, password, hashed_password):
        """Verify password dengan multiple algorithm support"""
        try:
            if not password or not hashed_password:
                return False
            
            # Check jika masih plaintext (existing users)
            if not hashed_password.startswith('sha256$'):
                # Fallback: compare plaintext untuk backward compatibility
                return password == hashed_password
            
            # Extract salt dan hash dari stored password
            parts = hashed_password.split('$')
            if len(parts) == 3:
                algorithm, salt, stored_hash = parts
                if algorithm == 'sha256':
                    # Hash input password dengan salt yang sama
                    new_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                    return new_hash == stored_hash
            
            return False
            
        except Exception as e:
            print(f"Password verification error: {e}")
            # Fallback ke plaintext comparison
            return password == hashed_password
    
    def sanitize_input(self, input_string):
        """Basic input sanitization untuk prevent injection"""
        if not input_string:
            return ""
        dangerous_chars = [';', "'", '"', '\\', '--', '/*', '*/', '`']
        sanitized = input_string
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
    
    def is_password_strong(self, password):
        """Validasi kekuatan password"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not any(char.isupper() for char in password):
            return False, "Password must contain uppercase letter"
        if not any(char.islower() for char in password):
            return False, "Password must contain lowercase letter" 
        if not any(char.isdigit() for char in password):
            return False, "Password must contain number"
        return True, "Password is strong"