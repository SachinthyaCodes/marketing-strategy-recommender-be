"""
User database service for managing user data in Supabase.
"""
from typing import Optional
from datetime import datetime
from supabase import create_client, Client

from app.models.user_models import UserCreate, UserInDB
from app.services.auth import get_password_hash
from app.config.settings import get_settings


class UserDatabaseService:
    """Service for user database operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        settings = get_settings()
        
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
        
        self.client: Client = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key
        )
        self.table_name = "users"
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        """
        Create a new user in the database.
        
        Args:
            user: UserCreate schema with email and password
            
        Returns:
            UserInDB with created user data
            
        Raises:
            Exception: If user already exists or database error occurs
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = get_password_hash(user.password)
        
        # Insert user into database
        user_data = {
            "email": user.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table(self.table_name).insert(user_data).execute()
        
        if not result.data:
            raise Exception("Failed to create user")
        
        user_dict = result.data[0]
        return UserInDB(**user_dict)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Retrieve a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            UserInDB if found, None otherwise
        """
        result = self.client.table(self.table_name).select("*").eq("email", email).execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        return UserInDB(**result.data[0])
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            UserInDB if found, None otherwise
        """
        result = self.client.table(self.table_name).select("*").eq("id", user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        return UserInDB(**result.data[0])


# Singleton instance
_user_db_service: Optional[UserDatabaseService] = None


def get_user_db_service() -> UserDatabaseService:
    """
    FastAPI dependency to get user database service instance.
    
    Returns:
        UserDatabaseService singleton instance
    """
    global _user_db_service
    
    if _user_db_service is None:
        _user_db_service = UserDatabaseService()
    
    return _user_db_service
