"""Authentication module for user login and role management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status  # type: ignore[import-untyped]
from fastapi.security import (  # type: ignore[import-untyped]
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt  # type: ignore[import-untyped]
from pydantic import BaseModel

# Secret key for JWT (in production, use environment variable)
SECRET_KEY = "pregnancy-med-checker-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


class UserRole(str, Enum):
    """User role types."""

    PROVIDER = "provider"
    PATIENT = "patient"


class User(BaseModel):
    """User model."""

    username: str
    role: UserRole
    full_name: str
    email: str


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"
    user: User


class TokenData(BaseModel):
    """Token data model."""

    username: str
    role: UserRole


# Test accounts (in production, use a database)
TEST_USERS = {
    "provider": {
        "username": "provider",
        "password": "provider123",  # In production, use hashed passwords
        "role": UserRole.PROVIDER,
        "full_name": "Dr. Sarah Johnson",
        "email": "sarah.johnson@hospital.com",
    },
    "patient": {
        "username": "patient",
        "password": "patient123",
        "role": UserRole.PATIENT,
        "full_name": "Sarah Williams",  # Test patient with pregnancy data, medications, and conditions (age 29)
        "email": "sarah.williams@example.com",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password (simplified for demo - use bcrypt in production)."""
    # For demo purposes, we're doing plain text comparison
    # In production, use: bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    return plain_password == hashed_password


def get_user(username: str) -> dict | None:
    """Get user by username."""
    return TEST_USERS.get(username)


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate user credentials."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")

        if username is None or username == "No username found":
            raise credentials_exception
        if role is None:
            raise credentials_exception
    except JWTError as e:
        # Provide more specific error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{username}' not found. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Handle role conversion - user["role"] is already a UserRole enum from TEST_USERS
    # but we need to ensure it's converted properly
    user_role = user["role"]
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid user role: {user_role}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return User(
        username=user["username"],
        role=user_role,
        full_name=user["full_name"],
        email=user["email"],
    )


async def get_current_provider(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure current user is a provider."""
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Provider access required.",
        )
    return current_user


async def get_current_patient(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure current user is a patient."""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Patient access required.",
        )
    return current_user
