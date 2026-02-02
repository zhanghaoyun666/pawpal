from app.database import supabase
import json

def check_pets():
    print("Checking Pets...")
    response = supabase.table("pets").select("*, owner:users(*)").execute()
    data = response.data
    print(f"Total Pets Found in DB: {len(data)}")
    for p in data:
        print(f"ID: {p['id']}, Name: {p['name']}, Owner: {p.get('owner', {}).get('name') if p.get('owner') else 'NONE'}")
        # Check for potentially problematic fields
        missing_fields = []
        for field in ['name', 'breed', 'age_text', 'age_value', 'image_url', 'category', 'location']:
            if p.get(field) is None:
                missing_fields.append(field)
        if missing_fields:
            print(f"  !!! Missing fields: {missing_fields}")

if __name__ == "__main__":
    check_pets()
