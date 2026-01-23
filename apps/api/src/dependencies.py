"""
Meeting Assistant - Dependencies
FastAPI dependency injection
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from .core.supabase import get_user_from_token

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get the current authenticated user
    
    Extracts and validates the JWT token from the Authorization header
    """
    token = credentials.credentials
    
    user = await get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Dependency to optionally get the current user
    
    Returns None if no valid token is provided (for public endpoints)
    """
    if not credentials:
        return None
    
    return await get_user_from_token(credentials.credentials)
