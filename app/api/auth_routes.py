"""
Authentication API routes for login and registration.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user_models import UserCreate, UserLogin, User, Token, TokenData
from app.services.user_database import UserDatabaseService, get_user_db_service
from app.services.auth import (
    verify_password,
    create_access_token,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    db_service: UserDatabaseService = Depends(get_user_db_service)
):
    """
    Register a new user.
    
    Args:
        user: UserCreate with email and password
        db_service: User database service dependency
        
    Returns:
        Created user without password
        
    Raises:
        HTTPException 400: If user already exists
        HTTPException 500: If database error occurs
    """
    try:
        logger.info(f"Attempting to register user: {user.email}")
        user_in_db = await db_service.create_user(user)
        logger.info(f"User created successfully: {user.email}")
        
        # Return user without hashed_password
        return User(
            id=user_in_db.id,
            email=user_in_db.email,
            created_at=user_in_db.created_at
        )
        
    except ValueError as e:
        logger.warning(f"Registration failed - user exists: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed with error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db_service: UserDatabaseService = Depends(get_user_db_service)
):
    """
    Login user and return JWT access token.
    
    Args:
        user_login: UserLogin with email and password
        db_service: User database service dependency
        
    Returns:
        Token with access_token and token_type
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Get user from database
    user = await db_service.get_user_by_email(user_login.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db_service: UserDatabaseService = Depends(get_user_db_service)
):
    """
    Get current user information from JWT token.
    
    This is a protected endpoint that requires a valid JWT token.
    
    Args:
        current_user: Current user from JWT token
        db_service: User database service dependency
        
    Returns:
        Current user information
        
    Raises:
        HTTPException 404: If user not found
    """
    user = await db_service.get_user_by_email(current_user.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@router.get("/protected")
async def protected_route(current_user: TokenData = Depends(get_current_user)):
    """
    Example protected route that requires authentication.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        Message with user email
    """
    return {
        "message": "This is a protected route",
        "user_email": current_user.email,
        "user_id": current_user.user_id
    }
