from app.database import supabase
import json

def check_missing_breeds():
    data = supabase.table("pets").select("name, breed").execute().data
    print(f"Total entries: {len(data)}")
    
    for item in data:
        if not item.get('breed'):
            print(f"Pet without breed: {item.get('name')}")

if __name__ == "__main__":
    check_missing_breeds()
