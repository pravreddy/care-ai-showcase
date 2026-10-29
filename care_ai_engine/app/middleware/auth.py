"""
Care AI Engine - Auth Middleware (Hardened)
FastAPI dependencies for authentication with token blacklist checking.

Every authenticated request now checks:
  1. Token is valid JWT (signature, expiry)
  2. Token type is "access"
  3. Token has NOT been blacklisted (logout/revocation)
  4. User exists and is active
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import decode_token, get_user_by_id, AuthError
from app.services.security_service import is_token_blacklisted
from app.models.database import User

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extract and validate JWT, return the current user.
    
    Now includes blacklist checking — tokens revoked via /auth/logout
    will be rejected immediately.
    
    Use as: current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials

    try:
        # Step 1: Check if token has been blacklisted (logout/revocation)
        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Step 2: Decode and validate JWT
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Step 3: Check user exists and is active
        user = await get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return user

    except HTTPException:
        raise
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
