from app.database import supabase
from app.models.schemas import Pet
import json
import traceback

def check_all_pets():
    print("Checking All Pets in DB and trying to validate each...")
    data = supabase.table("pets").select("*, owner:users(name, role, avatar_url)").execute().data
    print(f"Total pets in DB: {len(data)}")
    
    success_count = 0
    for item in data:
        pet_id = item.get('id')
        pet_name = item.get('name')
        
        # Apply mapping exactly as in pets.py
        transformed = item.copy()
        owner_data = transformed.get('owner')
        if owner_data:
            # Map avatar_url to image
            owner_data['image'] = owner_data.pop('avatar_url', '') or ''
            
        # Map age_text to age
        if 'age_text' in transformed:
            transformed['age'] = transformed.pop('age_text') or '未知'
        else:
            transformed['age'] = '未知'

        # Ensure ageValue is int
        if 'age_value' in transformed:
             transformed['ageValue'] = int(transformed.pop('age_value')) if transformed.get('age_value') is not None else 0
        else:
            transformed['ageValue'] = 0
             
        # Map health_info to health
        if 'health_info' in transformed:
            transformed['health'] = transformed.pop('health_info')
            
        # Map image_url to image
        if 'image_url' in transformed:
            transformed['image'] = transformed.pop('image_url') or ''
        else:
            transformed['image'] = ''
            
        # Map location to distance (for display)
        if 'location' in transformed:
            loc = transformed.get('location', '') or '未知'
            transformed['distance'] = loc.replace(' ', '，') if ' ' in loc else loc
        else:
            transformed['distance'] = '未知'

        try:
            # This is what FastAPI does internally
            Pet.model_validate(transformed)
            print(f"  [SUCCESS] Validated {pet_name}")
            success_count += 1
        except Exception as e:
            print(f"\n[FAILURE] Validation error for {pet_name} ({pet_id}):")
            print(f"  Error: {e}")
            print(f"  Transformed Data: {json.dumps(transformed, indent=2, ensure_ascii=False)}")
            # Specifically check gender and category
            print(f"  Category: {transformed.get('category')}")
            print(f"  Gender: {transformed.get('gender')}")

    print(f"\nSummary: {success_count}/{len(data)} pets passed validation.")

if __name__ == "__main__":
    check_all_pets()
