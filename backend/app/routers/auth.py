from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.models.schemas import UserCreate, UserLogin, Token, User
from app.auth_utils import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=User)
def register(user: UserCreate):
    # Check if user exists
    existing = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = {
        "email": user.email,
        "password_hash": hashed_password,
        "name": user.name or user.email.split("@")[0],
        "role": user.role,
        "avatar_url": user.avatar_url
    }

    response = supabase.table("users").insert(new_user).execute()
    if not response.data:
         raise HTTPException(status_code=500, detail="Failed to register user")
    
    return response.data[0]

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin):
    # Get user
    response = supabase.table("users").select("*").eq("email", user_credentials.email).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = response.data[0]
    if not verify_password(user_credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Create token
    access_token = create_access_token(data={"sub": user['id'], "role": user['role']})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }
