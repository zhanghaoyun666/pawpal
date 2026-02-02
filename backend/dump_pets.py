from app.database import supabase
import json

def dump_data():
    data = supabase.table("pets").select("*, owner:users(*)").execute().data
    print(f"Total entries: {len(data)}")
    
    transformed_list = []
    for item in data:
        transformed = item.copy()
        owner_data = transformed.get('owner')
        if owner_data:
            owner_data['image'] = owner_data.pop('avatar_url', '') or ''
            
        if 'age_text' in transformed:
            transformed['age'] = transformed.pop('age_text') or '未知'
        else:
            transformed['age'] = '未知'

        if 'age_value' in transformed:
             transformed['ageValue'] = int(transformed.pop('age_value')) if transformed.get('age_value') is not None else 0
        else:
            transformed['ageValue'] = 0
             
        if 'health_info' in transformed:
            transformed['health'] = transformed.pop('health_info')
            
        if 'image_url' in transformed:
            transformed['image'] = transformed.pop('image_url') or ''
        else:
            transformed['image'] = ''
            
        if 'location' in transformed:
            loc = transformed.get('location', '') or '未知'
            transformed['distance'] = loc.replace(' ', '，') if ' ' in loc else loc
        else:
            transformed['distance'] = '未知'
            
        transformed_list.append(transformed)
        
    print(json.dumps(transformed_list, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    dump_data()
