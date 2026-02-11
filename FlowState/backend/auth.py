
"""
Authentication System for FlowState
Uses Supabase Auth for user management
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import jwt
from datetime import datetime, timedelta

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cszoklkfdszqsxhufhhj.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")

security = HTTPBearer()


class AuthService:
    """Handle authentication with Supabase"""

    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.anon_key = SUPABASE_ANON_KEY

    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> dict:
        """Verify JWT token from Supabase"""
        token = credentials.credentials

        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )

            # Check expiration
            if payload.get("exp", 0) < datetime.now().timestamp():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )

            return payload

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user"""
        payload = await self.verify_token(credentials)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }

    async def signup(self, email: str, password: str) -> dict:
        """Create new user account"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/auth/v1/signup",
                json={"email": email, "password": password},
                headers={"apikey": self.anon_key}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create account"
                )

            return response.json()

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/auth/v1/token?grant_type=password",
                json={"email": email, "password": password},
                headers={"apikey": self.anon_key}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            return response.json()


auth_service = AuthService()
