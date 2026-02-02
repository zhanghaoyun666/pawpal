from app.database import supabase
import json

def check_field_values():
    data = supabase.table("pets").select("name, gender, category").execute().data
    print(f"Total entries: {len(data)}")
    
    genders = set()
    categories = set()
    
    for item in data:
        genders.add(item.get('gender'))
        categories.add(item.get('category'))
        if item.get('gender') not in ['Male', 'Female', None]:
            print(f"Unusual Gender: '{item.get('gender')}' in pet '{item.get('name')}'")
        if item.get('category') not in ['dog', 'cat', 'rabbit', 'other']:
            print(f"Unusual Category: '{item.get('category')}' in pet '{item.get('name')}'")

    print(f"\nUnique Genders: {genders}")
    print(f"Unique Categories: {categories}")

if __name__ == "__main__":
    check_field_values()
