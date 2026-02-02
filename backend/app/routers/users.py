from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.database import supabase
from app.auth_utils import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/favorites", response_model=List[str])
def get_favorites(current_user = Depends(get_current_user)):
    # Return list of pet IDs for the authenticated user
    response = supabase.table("favorites").select("pet_id").eq("user_id", current_user.id).execute()
    return [item['pet_id'] for item in response.data]

@router.post("/favorites/{pet_id}")
def toggle_favorite(pet_id: str, current_user = Depends(get_current_user)):
    # Check if exists for the authenticated user
    response = supabase.table("favorites").select("*").eq("user_id", current_user.id).eq("pet_id", pet_id).execute()
    
    if response.data:
        # Remove
        supabase.table("favorites").delete().eq("user_id", current_user.id).eq("pet_id", pet_id).execute()
        return {"status": "removed"}
    else:
        # Add
        supabase.table("favorites").insert({"user_id": current_user.id, "pet_id": pet_id}).execute()
        return {"status": "added"}