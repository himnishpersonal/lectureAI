"""Usage tracking service for API limits and resource management."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models import UserDB, DocumentDB

logger = logging.getLogger(__name__)

class UsageService:
    """Service for tracking user usage and enforcing limits."""
    
    def __init__(self):
        self.default_daily_api_limit = 100
        self.default_storage_limit_bytes = 1073741824  # 1GB
    
    def check_api_limit(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Check if user has exceeded daily API limit."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"allowed": False, "error": "User not found"}
            
            # Reset daily counter if it's a new day
            if user.last_login and user.last_login.date() < datetime.utcnow().date():
                user.daily_api_calls = 0
                db.commit()
            
            if user.daily_api_calls >= user.daily_api_limit:
                return {
                    "allowed": False,
                    "error": "Daily API limit exceeded",
                    "current_usage": user.daily_api_calls,
                    "limit": user.daily_api_limit
                }
            
            return {
                "allowed": True,
                "current_usage": user.daily_api_calls,
                "limit": user.daily_api_limit,
                "remaining": user.daily_api_limit - user.daily_api_calls
            }
            
        except Exception as e:
            logger.error(f"Error checking API limit for user {user_id}: {str(e)}")
            return {"allowed": False, "error": "Failed to check API limit"}
    
    def increment_api_usage(self, user_id: int, db: Session) -> bool:
        """Increment user's daily API usage counter."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return False
            
            # Reset daily counter if it's a new day
            if user.last_login and user.last_login.date() < datetime.utcnow().date():
                user.daily_api_calls = 0
            
            user.daily_api_calls += 1
            db.commit()
            
            logger.debug(f"Incremented API usage for user {user.username}: {user.daily_api_calls}/{user.daily_api_limit}")
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing API usage for user {user_id}: {str(e)}")
            db.rollback()
            return False
    
    def check_storage_limit(self, user_id: int, additional_bytes: int, db: Session) -> Dict[str, Any]:
        """Check if user has enough storage space for additional data."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"allowed": False, "error": "User not found"}
            
            if user.total_storage_bytes + additional_bytes > user.storage_limit_bytes:
                return {
                    "allowed": False,
                    "error": "Storage limit exceeded",
                    "current_usage": user.total_storage_bytes,
                    "limit": user.storage_limit_bytes,
                    "additional_requested": additional_bytes
                }
            
            return {
                "allowed": True,
                "current_usage": user.total_storage_bytes,
                "limit": user.storage_limit_bytes,
                "additional_requested": additional_bytes,
                "remaining": user.storage_limit_bytes - user.total_storage_bytes
            }
            
        except Exception as e:
            logger.error(f"Error checking storage limit for user {user_id}: {str(e)}")
            return {"allowed": False, "error": "Failed to check storage limit"}
    
    def update_storage_usage(self, user_id: int, additional_bytes: int, db: Session) -> bool:
        """Update user's storage usage."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return False
            
            user.total_storage_bytes += additional_bytes
            db.commit()
            
            logger.debug(f"Updated storage usage for user {user.username}: {user.total_storage_bytes} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error updating storage usage for user {user_id}: {str(e)}")
            db.rollback()
            return False
    
    def update_document_count(self, user_id: int, increment: int, db: Session) -> bool:
        """Update user's document count."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return False
            
            user.total_documents += increment
            db.commit()
            
            logger.debug(f"Updated document count for user {user.username}: {user.total_documents}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document count for user {user_id}: {str(e)}")
            db.rollback()
            return False
    
    def get_user_usage_stats(self, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get comprehensive usage statistics for a user."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return None
            
            # Calculate storage usage percentage
            storage_percentage = (user.total_storage_bytes / user.storage_limit_bytes) * 100 if user.storage_limit_bytes > 0 else 0
            
            # Calculate API usage percentage
            api_percentage = (user.daily_api_calls / user.daily_api_limit) * 100 if user.daily_api_limit > 0 else 0
            
            return {
                "user_id": user_id,
                "username": user.username,
                "api_usage": {
                    "daily_calls": user.daily_api_calls,
                    "daily_limit": user.daily_api_limit,
                    "percentage": round(api_percentage, 2),
                    "remaining": user.daily_api_limit - user.daily_api_calls
                },
                "storage_usage": {
                    "used_bytes": user.total_storage_bytes,
                    "limit_bytes": user.storage_limit_bytes,
                    "percentage": round(storage_percentage, 2),
                    "remaining_bytes": user.storage_limit_bytes - user.total_storage_bytes,
                    "used_mb": round(user.total_storage_bytes / (1024 * 1024), 2),
                    "limit_mb": round(user.storage_limit_bytes / (1024 * 1024), 2)
                },
                "document_count": user.total_documents
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {str(e)}")
            return None
    
    def reset_daily_usage(self, user_id: int, db: Session) -> bool:
        """Reset daily API usage counter for a user."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return False
            
            user.daily_api_calls = 0
            db.commit()
            
            logger.info(f"Reset daily API usage for user {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting daily usage for user {user_id}: {str(e)}")
            db.rollback()
            return False
    
    def update_user_limits(self, user_id: int, limits: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Update user's usage limits (admin only)."""
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Update allowed limit fields
            if "daily_api_limit" in limits:
                user.daily_api_limit = limits["daily_api_limit"]
            
            if "storage_limit_bytes" in limits:
                user.storage_limit_bytes = limits["storage_limit_bytes"]
            
            db.commit()
            
            logger.info(f"Updated limits for user {user.username}")
            
            return {
                "success": True,
                "message": "User limits updated successfully",
                "new_limits": {
                    "daily_api_limit": user.daily_api_limit,
                    "storage_limit_bytes": user.storage_limit_bytes
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating limits for user {user_id}: {str(e)}")
            return {"success": False, "error": "Failed to update limits"}
    
    def cleanup_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Clean up user data when account is deleted."""
        try:
            # Get user's total storage usage from documents
            total_storage = db.query(DocumentDB).join(UserDB.courses).filter(
                UserDB.id == user_id
            ).with_entities(db.func.sum(DocumentDB.file_size)).scalar() or 0
            
            # Get document count
            document_count = db.query(DocumentDB).join(UserDB.courses).filter(
                UserDB.id == user_id
            ).count()
            
            logger.info(f"Cleaning up data for user {user_id}: {document_count} documents, {total_storage} bytes")
            
            return {
                "success": True,
                "documents_deleted": document_count,
                "storage_freed": total_storage
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up data for user {user_id}: {str(e)}")
            return {"success": False, "error": "Failed to cleanup user data"}
