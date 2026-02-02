from app.database import supabase
from app.models.applications_schema import Application
from typing import List

def test_apps():
    target_id = "08e77f74-292f-4427-af83-a331d55ec20d"
    print("Trying select pet:pets(*)...")
    try:
        response = supabase.table("applications").select("*, pet:pets(*)").limit(2).execute()
        print("Success with pet:pets(*)!")
        if response.data:
            print(f"Keys in pet: {response.data[0].get('pet', {}).keys()}")
    except Exception as e:
        print(f"Failed with pet:pets(*): {e}")
    
    for item in data:
        if item.get("pet"):
            # The transformation we implemented in applications.py
            orig_pet = item["pet"].copy()
            item["pet"]["image"] = item["pet"].pop("image_url", "") or ""
            
        try:
            Application(**item)
            print(f"App {item['id']}: VALID")
        except Exception as e:
            print(f"App {item['id']}: INVALID")
            print(f"Error: {e}")
            print(f"Data: {item}")

if __name__ == "__main__":
    test_apps()
