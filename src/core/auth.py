"""
Authentication system for F-OSINT DWv1
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from utils.encryption import PasswordManager, DataEncryption, generate_session_token
from utils.file_utils import get_data_dir, save_json, load_json


class User:
    """User model"""
    
    def __init__(self, username: str, email: str, password_hash: str, 
                 user_id: str = None, created_at: str = None, 
                 last_login: str = None, is_active: bool = True):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = last_login
        self.is_active = is_active
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        return cls(**data)


class AuthManager:
    """Authentication manager"""
    
    def __init__(self):
        self.users_file = os.path.join(get_data_dir(), 'users', 'users.json')
        self.password_manager = PasswordManager()
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, User]:
        """Load users from file"""
        users_data = load_json(self.users_file)
        if not users_data:
            return {}
        
        users = {}
        for user_id, user_data in users_data.items():
            users[user_id] = User.from_dict(user_data)
        return users
    
    def _save_users(self) -> bool:
        """Save users to file"""
        users_data = {}
        for user_id, user in self.users.items():
            users_data[user_id] = user.to_dict()
        
        return save_json(users_data, self.users_file)
    
    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Register a new user"""
        # Check if username or email already exists
        for user in self.users.values():
            if user.username == username:
                raise ValueError("Username already exists")
            if user.email == email:
                raise ValueError("Email already exists")
        
        # Validate password strength
        if not self._validate_password(password):
            raise ValueError("Password does not meet requirements")
        
        # Create new user
        password_hash = self.password_manager.hash_password(password)
        user = User(username=username, email=email, password_hash=password_hash)
        
        # Save user
        self.users[user.user_id] = user
        if self._save_users():
            return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        for user in self.users.values():
            if user.username == username and user.is_active:
                if self.password_manager.verify_password(password, user.password_hash):
                    # Update last login
                    user.last_login = datetime.now().isoformat()
                    self._save_users()
                    return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def update_user_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user.password_hash):
            return False
        
        # Validate new password
        if not self._validate_password(new_password):
            raise ValueError("New password does not meet requirements")
        
        # Update password
        user.password_hash = self.password_manager.hash_password(new_password)
        return self._save_users()
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            return self._save_users()
        return False
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        return len(self.users)
    
    def get_active_user_count(self) -> int:
        """Get number of active users"""
        return sum(1 for user in self.users.values() if user.is_active)