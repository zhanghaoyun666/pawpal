import asyncio
import os
from dotenv import load_dotenv
from app.database import supabase
from app.auth_utils import get_password_hash

# Load environment variables
load_dotenv()

def update_passwords():
    print("Updating passwords for default users...")
    
    default_password = "password123"
    hashed_password = get_password_hash(default_password)
    
    users_to_update = [
        "test@example.com",
        "sarah@example.com"
    ]
    
    for email in users_to_update:
        print(f"Updating password for {email}...")
        response = supabase.table("users").update({"password_hash": hashed_password}).eq("email", email).execute()
        if response.data:
            print(f"Successfully updated password for {email}")
        else:
            print(f"User {email} not found or update failed (maybe already correct)")

if __name__ == "__main__":
    update_passwords()
