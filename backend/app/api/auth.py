"""
Authentication API endpoints.
Login, register, and role-based access control.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib

from ..core.db import get_db
from ..models.user import User, CandidateUserProfile, AdminUserProfile

router = APIRouter()

# JWT settings
SECRET_KEY = "vibecode-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Bearer token
security = HTTPBearer(auto_error=False)


# ========== Schemas ==========

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "candidate"  # candidate | admin


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str
    full_name: Optional[str]


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Helper functions ==========

def hash_password(password: str) -> str:
    """Simple SHA256 hash for demo purposes."""
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except JWTError:
        return None


def require_role(*allowed_roles: str):
    """Dependency to require specific roles."""
    async def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        try:
            token = credentials.credentials
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            
            return user
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    return dependency


# ========== Endpoints ==========

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if user_data.role not in ["candidate", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'candidate' or 'admin'"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create profile based on role
    if user.role == "candidate":
        profile = CandidateUserProfile(user_id=user.id)
        db.add(profile)
    else:
        profile = AdminUserProfile(user_id=user.id)
        db.add(profile)
    db.commit()
    
    # Generate token
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_role("candidate", "admin"))):
    """Get current user info."""
    return user


@router.post("/demo/candidate", response_model=TokenResponse)
async def demo_candidate_login(db: Session = Depends(get_db)):
    """Quick demo login as candidate (for testing)."""
    email = "demo_candidate@vibecode.ai"
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password("demo123"),
            full_name="Demo Candidate",
            role="candidate"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        profile = CandidateUserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
    
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


@router.post("/demo/admin", response_model=TokenResponse)
async def demo_admin_login(db: Session = Depends(get_db)):
    """Quick demo login as admin (for testing)."""
    email = "demo_admin@vibecode.ai"
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password("demo123"),
            full_name="Demo Recruiter",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        profile = AdminUserProfile(user_id=user.id, company_name="VibeCode Inc.")
        db.add(profile)
        db.commit()
    
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


# пидормот
