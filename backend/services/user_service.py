"""User service for user management operations."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import UserDB, UserCreate, UserResponse, UserLogin
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations."""
    
    def __init__(self, auth_service: Optional[AuthService] = None):
        self.auth_service = auth_service or AuthService()
    
    def create_user(self, user_data: UserCreate, db: Session) -> Dict[str, Any]:
        """Create a new user."""
        try:
            # Check if username or email already exists
            existing_user = db.query(UserDB).filter(
                (UserDB.username == user_data.username) | 
                (UserDB.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    return {"success": False, "error": "Username already exists"}
                else:
                    return {"success": False, "error": "Email already exists"}
            
            # Hash password
            password_hash = self.auth_service.hash_password(user_data.password)
            
            # Create user
            user = UserDB(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                role="user"  # Default role
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created user: {user.username} (ID: {user.id})")
            
            return {
                "success": True,
                "user": UserResponse.from_orm(user),
                "message": "User created successfully"
            }
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating user {user_data.username}: {str(e)}")
            return {"success": False, "error": "Username or email already exists"}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user {user_data.username}: {str(e)}")
            return {"success": False, "error": "Failed to create user"}
    
    def authenticate_user(self, login_data: UserLogin, db: Session) -> Dict[str, Any]:
        """Authenticate a user and return session info."""
        try:
            # Find user by username
            user = db.query(UserDB).filter(
                UserDB.username == login_data.username,
                UserDB.is_active == True
            ).first()
            
            if not user:
                logger.warning(f"Login attempt for non-existent user: {login_data.username}")
                return {"success": False, "error": "Invalid username or password"}
            
            # Verify password
            if not self.auth_service.verify_password(login_data.password, user.password_hash):
                logger.warning(f"Invalid password for user: {user.username}")
                return {"success": False, "error": "Invalid username or password"}
            
            # Create session
            session = self.auth_service.create_session(user, db)
            
            logger.info(f"User {user.username} logged in successfully")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "user": UserResponse.from_orm(user),
                "expires_at": session.expires_at,
                "message": "Login successful"
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user {login_data.username}: {str(e)}")
            return {"success": False, "error": "Authentication failed"}
    
    def get_user_by_id(self, user_id: int, db: Session) -> Optional[UserResponse]:
        """Get user by ID."""
        try:
            user = db.query(UserDB).filter(
                UserDB.id == user_id,
                UserDB.is_active == True
            ).first()
            
            if user:
                return UserResponse.from_orm(user)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str, db: Session) -> Optional[UserResponse]:
        """Get user by username."""
        try:
            user = db.query(UserDB).filter(
                UserDB.username == username,
                UserDB.is_active == True
            ).first()
            
            if user:
                return UserResponse.from_orm(user)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {username}: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: int, updates: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Update user profile information."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Update allowed fields
            allowed_fields = ["email"]
            for field, value in updates.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Updated profile for user {user.username}")
            
            return {
                "success": True,
                "user": UserResponse.from_orm(user),
                "message": "Profile updated successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return {"success": False, "error": "Failed to update profile"}
    
    def change_password(self, user_id: int, old_password: str, new_password: str, db: Session) -> Dict[str, Any]:
        """Change user password."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify old password
            if not self.auth_service.verify_password(old_password, user.password_hash):
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash new password
            new_password_hash = self.auth_service.hash_password(new_password)
            user.password_hash = new_password_hash
            
            db.commit()
            
            # Invalidate all existing sessions
            self.auth_service.invalidate_user_sessions(user_id, db)
            
            logger.info(f"Password changed for user {user.username}")
            
            return {
                "success": True,
                "message": "Password changed successfully. Please log in again."
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error changing password for user {user_id}: {str(e)}")
            return {"success": False, "error": "Failed to change password"}
    
    def deactivate_user(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Deactivate a user account."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            user.is_active = False
            db.commit()
            
            # Invalidate all sessions
            self.auth_service.invalidate_user_sessions(user_id, db)
            
            logger.info(f"Deactivated user {user.username}")
            
            return {
                "success": True,
                "message": "User account deactivated"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            return {"success": False, "error": "Failed to deactivate user"}
    
    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users (admin only)."""
        try:
            users = db.query(UserDB).filter(UserDB.is_active == True).offset(skip).limit(limit).all()
            return [UserResponse.from_orm(user) for user in users]
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []
    
    def create_admin_user(self, username: str, email: str, password: str, db: Session) -> Dict[str, Any]:
        """Create an admin user."""
        try:
            # Check if admin already exists
            existing_admin = db.query(UserDB).filter(UserDB.role == "admin").first()
            if existing_admin:
                return {"success": False, "error": "Admin user already exists"}
            
            # Hash password
            password_hash = self.auth_service.hash_password(password)
            
            # Create admin user
            admin_user = UserDB(
                username=username,
                email=email,
                password_hash=password_hash,
                role="admin",
                daily_api_limit=1000,  # Higher limit for admin
                storage_limit_bytes=10737418240  # 10GB for admin
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            logger.info(f"Created admin user: {admin_user.username} (ID: {admin_user.id})")
            
            return {
                "success": True,
                "user": UserResponse.from_orm(admin_user),
                "message": "Admin user created successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
            return {"success": False, "error": "Failed to create admin user"}
