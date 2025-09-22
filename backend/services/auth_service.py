"""Authentication service for user management."""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt

from ..models import UserDB, UserSessionDB
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.session_duration_hours = 24  # Sessions last 24 hours by default
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            return password_hash.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            raise ValueError("Failed to hash password")
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    def create_session(
        self, 
        user: UserDB, 
        db: Session, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSessionDB:
        """Create a new user session."""
        try:
            # Generate session ID
            session_id = self.generate_session_id()
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(hours=self.session_duration_hours)
            
            # Create session
            session = UserSessionDB(
                session_id=session_id,
                user_id=user.id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(session)
            db.commit()
            
            # Update user's last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            logger.info(f"Created session for user {user.username} (ID: {user.id})")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session for user {user.username}: {str(e)}")
            db.rollback()
            raise
    
    def validate_session(self, session_id: str, db: Session) -> Optional[UserDB]:
        """Validate a session and return the associated user."""
        try:
            # Find active session
            session = db.query(UserSessionDB).filter(
                UserSessionDB.session_id == session_id,
                UserSessionDB.is_active == True,
                UserSessionDB.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                logger.debug(f"Invalid or expired session: {session_id}")
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
            
            # Get user
            user = db.query(UserDB).filter(
                UserDB.id == session.user_id,
                UserDB.is_active == True
            ).first()
            
            if not user:
                logger.warning(f"Session {session_id} references inactive user")
                return None
            
            logger.debug(f"Validated session for user {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {str(e)}")
            return None
    
    def invalidate_session(self, session_id: str, db: Session) -> bool:
        """Invalidate a session."""
        try:
            session = db.query(UserSessionDB).filter(
                UserSessionDB.session_id == session_id
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                logger.info(f"Invalidated session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating session {session_id}: {str(e)}")
            db.rollback()
            return False
    
    def invalidate_user_sessions(self, user_id: int, db: Session) -> int:
        """Invalidate all sessions for a user."""
        try:
            sessions = db.query(UserSessionDB).filter(
                UserSessionDB.user_id == user_id,
                UserSessionDB.is_active == True
            ).all()
            
            count = 0
            for session in sessions:
                session.is_active = False
                count += 1
            
            db.commit()
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating sessions for user {user_id}: {str(e)}")
            db.rollback()
            return 0
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions."""
        try:
            expired_sessions = db.query(UserSessionDB).filter(
                UserSessionDB.expires_at < datetime.utcnow(),
                UserSessionDB.is_active == True
            ).all()
            
            count = 0
            for session in expired_sessions:
                session.is_active = False
                count += 1
            
            db.commit()
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            db.rollback()
            return 0
    
    def get_user_sessions(self, user_id: int, db: Session) -> list[UserSessionDB]:
        """Get all active sessions for a user."""
        try:
            return db.query(UserSessionDB).filter(
                UserSessionDB.user_id == user_id,
                UserSessionDB.is_active == True,
                UserSessionDB.expires_at > datetime.utcnow()
            ).all()
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []
