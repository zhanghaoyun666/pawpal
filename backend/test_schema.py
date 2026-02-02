from app.database import supabase
from app.models.schemas import Pet
from typing import List
import json

def test_transformation():
    query = supabase.table("pets").select("*, owner:users(name, role, avatar_url)")
    response = query.execute()
    data = response.data
    
    print(f"Original items from DB: {len(data)}")
    
    formatted_data = []
    for item in data:
        try:
            # Replicating pets.py logic
            owner_data = item.get('owner')
            if owner_data:
                owner_data['image'] = owner_data.pop('avatar_url', '')
                
            if 'age_text' in item:
                item['age'] = item.pop('age_text')

            if 'age_value' in item:
                 item['ageValue'] = item.pop('age_value')
                 
            if 'health_info' in item:
                item['health'] = item.pop('health_info')
                
            if 'image_url' in item:
                item['image'] = item.pop('image_url')
                
            if 'location' in item:
                loc = item.get('location', '')
                item['distance'] = loc.replace(' ', '，') if ' ' in loc else loc
            else:
                item['distance'] = 'Unknown'

            # Try to validate with Pydantic
            Pet.model_validate(item)
            formatted_data.append(item)
        except Exception as e:
            print(f"Validation failed for pet {item.get('id', 'unknown')}: {e}")
            # print(f"Problematic item: {json.dumps(item, indent=2)}")

    print(f"Successfully validated items: {len(formatted_data)}")

if __name__ == "__main__":
    test_transformation()
