"""
Session management for F-OSINT DWv1
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from utils.encryption import DataEncryption, generate_session_token
from utils.file_utils import get_sessions_dir, save_json, load_json
from core.auth import User


class Session:
    """User session model"""
    
    def __init__(self, session_id: str, user_id: str, username: str,
                 created_at: str = None, expires_at: str = None,
                 last_activity: str = None, data: Dict[str, Any] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.created_at = created_at or datetime.now().isoformat()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24)).isoformat()
        self.last_activity = last_activity or datetime.now().isoformat()
        self.data = data or {}
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        now = datetime.now()
        expires = datetime.fromisoformat(self.expires_at)
        return now < expires
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now().isoformat()
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        new_expiry = datetime.now() + timedelta(hours=hours)
        self.expires_at = new_expiry.isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'last_activity': self.last_activity,
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary"""
        return cls(**data)


class SessionManager:
    """Session manager"""
    
    def __init__(self):
        self.sessions_dir = get_sessions_dir()
        self.current_session = None
        self.encryption = None
    
    def start_session(self, user: User, remember_me: bool = False) -> Session:
        """Start a new session for user"""
        # Generate session token
        session_id = generate_session_token()
        
        # Create session
        hours = 24 * 7 if remember_me else 24  # 7 days if remember me, else 24 hours
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            username=user.username
        )
        session.extend_session(hours)
        
        # Initialize encryption for session data
        self.encryption = DataEncryption(session_id)
        
        # Save session
        self._save_session(session)
        
        # Set as current session
        self.current_session = session
        
        return session
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session from storage"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        session_data = load_json(session_file)
        
        if session_data:
            session = Session.from_dict(session_data)
            if session.is_valid():
                session.update_activity()
                self._save_session(session)
                self.current_session = session
                self.encryption = DataEncryption(session_id)
                return session
            else:
                # Clean up expired session
                self._delete_session(session_id)
        
        return None
    
    def end_session(self, session_id: str = None):
        """End a session"""
        if session_id is None and self.current_session:
            session_id = self.current_session.session_id
        
        if session_id:
            self._delete_session(session_id)
        
        self.current_session = None
        self.encryption = None
    
    def has_valid_session(self) -> bool:
        """Check if there's a valid current session"""
        return self.current_session is not None and self.current_session.is_valid()
    
    def get_session_data(self, key: str) -> Any:
        """Get data from current session"""
        if self.current_session and key in self.current_session.data:
            encrypted_data = self.current_session.data[key]
            if self.encryption:
                return self.encryption.decrypt(encrypted_data)
        return None
    
    def set_session_data(self, key: str, value: Any):
        """Set data in current session"""
        if self.current_session and self.encryption:
            encrypted_value = self.encryption.encrypt(str(value))
            if encrypted_value:
                self.current_session.data[key] = encrypted_value
                self._save_session(self.current_session)
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self.current_session.user_id if self.current_session else None
    
    def get_current_username(self) -> Optional[str]:
        """Get current username"""
        return self.current_session.username if self.current_session else None
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions"""
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json extension
                session_file = os.path.join(self.sessions_dir, filename)
                session_data = load_json(session_file)
                
                if session_data:
                    session = Session.from_dict(session_data)
                    if not session.is_valid():
                        self._delete_session(session_id)
    
    def _save_session(self, session: Session):
        """Save session to file"""
        session_file = os.path.join(self.sessions_dir, f"{session.session_id}.json")
        save_json(session.to_dict(), session_file)
    
    def _delete_session(self, session_id: str):
        """Delete session file"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        count = 0
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('.json'):
                session_file = os.path.join(self.sessions_dir, filename)
                session_data = load_json(session_file)
                if session_data:
                    session = Session.from_dict(session_data)
                    if session.is_valid():
                        count += 1
        return count