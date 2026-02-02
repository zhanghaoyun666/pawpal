from app.database import supabase
from app.models.applications_schema import Application
from typing import List

def run_diag():
    print("Fetching applications...")
    try:
        response = supabase.table("applications").select("*, pet:pets(*)").execute()
        data = response.data
        print(f"Found {len(data)} applications")
        
        for i, item in enumerate(data):
            if item.get("pet"):
                # Apply the transformation
                item["pet"]["image"] = item["pet"].pop("image_url", "") or ""
            
            try:
                # Attempt to validate with Pydantic
                app_obj = Application(**item)
                print(f"[{i}] {item['id']}: OK")
            except Exception as e:
                print(f"[{i}] {item['id']}: FAIL")
                print(f"  Error: {e}")
                
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    run_diag()
