from fastapi import APIRouter, HTTPException
from typing import List
from app.database import supabase
from app.models.schemas import Pet, PetCreate

router = APIRouter(prefix="/api/pets", tags=["pets"])

@router.post("/", response_model=Pet)
def create_pet(pet: PetCreate):
    pet_data = pet.model_dump()
    # Remove any None values to allow DB defaults to kick in if needed
    pet_data = {k: v for k, v in pet_data.items() if v is not None}
    
    print(f"DEBUG: Creating pet with data: {pet_data}")
    
    try:
        response = supabase.table("pets").insert(pet_data).execute()
        
        # Check for errors in the response object (some versions of postgrest return it this way)
        if hasattr(response, 'error') and response.error:
            print(f"DEBUG: Supabase error: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
            
        if not response.data:
            print(f"DEBUG: Failed to create pet. Empty response data. Response: {response}")
            raise HTTPException(status_code=500, detail="Failed to create pet: No data returned")
            
        item = response.data[0]
    except Exception as e:
        print(f"DEBUG: Exception in create_pet: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Transformation to match Pet response model
    if 'age_text' in item:
        item['age'] = item.pop('age_text') or '未知'
    else:
        item['age'] = '未知'
        
    if 'age_value' in item:
        item['ageValue'] = int(item.pop('age_value')) if item.get('age_value') is not None else 0
    else:
        item['ageValue'] = 0
        
    if 'health_info' in item:
        item['health'] = item.pop('health_info')
    if 'image_url' in item:
        item['image'] = item.pop('image_url') or ''
    else:
        item['image'] = ''
        
    if 'location' in item:
        loc = item.get('location', '') or '未知'
        item['distance'] = loc.replace(' ', '，') if ' ' in loc else loc
    else:
        item['distance'] = '未知'
        
    print(f"DEBUG: Successfully created pet: {item['id']}")
    return item

def _check_if_adopted(pet_id: str):
    """
    Helper to check if a pet has been adopted by checking if there's an approved application for it.
    """
    try:
        response = supabase.table("applications").select("*").eq("pet_id", pet_id).eq("status", "approved").execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"DEBUG: Error checking adoption status: {str(e)}")
        return False


def _format_pet(item, is_adopted=False):
    """
    Helper to transform a DB pet record to the Pet Pydantic model.
    """
    if not item:
        return None
        
    # Map owner data
    owner_data = item.get('owner')
    if isinstance(owner_data, dict):
        # Database key is avatar_url, Pydantic key is image
        avatar = owner_data.get('avatar_url')
        if avatar:
            owner_data['image'] = str(avatar)
        else:
            # Check if image already exists and is not None
            current_image = owner_data.get('image')
            if current_image:
                owner_data['image'] = str(current_image)
            else:
                # Provide a default avatar
                owner_data['image'] = f"https://api.dicebear.com/7.x/avataaars/svg?seed={owner_data.get('name', 'default')}"
            
        # Ensure name and role are strings too
        owner_data['name'] = str(owner_data.get('name') or "未知")
        owner_data['role'] = str(owner_data.get('role') or "用户")
        
        # Clean up DB field
        if 'avatar_url' in owner_data:
            del owner_data['avatar_url']
        
    # Map age fields
    # The Pydantic model 'Pet' requires 'age' (str) and 'ageValue' (int)
    if 'age_text' in item:
        item['age'] = item.pop('age_text') or '未知'
    elif 'age' not in item:
        item['age'] = '未知'
        
    if 'age_value' in item:
        item['ageValue'] = int(item.pop('age_value')) if item.get('age_value') is not None else 0
    elif 'ageValue' not in item:
        item['ageValue'] = 0
        
    # Map health_info to health
    if 'health_info' in item:
        item['health'] = item.pop('health_info')
        
    # Map image_url to image
    if 'image_url' in item:
        item['image'] = item.pop('image_url') or ''
    elif 'image' not in item:
        item['image'] = ''
        
    # Map location to distance (for display)
    if 'location' in item:
        loc = item.get('location', '') or '未知'
        item['distance'] = loc.replace(' ', '，') if ' ' in loc else loc
    elif 'distance' not in item:
        item['distance'] = '未知'
        
    # Ensure category is present (it's a Literal in Pydantic)
    if not item.get('category'):
        item['category'] = 'other'
        
    # Ensure tags is a list
    if item.get('tags') is None:
        item['tags'] = []
        
    # Add adoption status
    item['isAdopted'] = is_adopted
        
    return item

@router.get("/", response_model=List[Pet])
def get_pets(owner_id: str = None):
    # Fetch pets with owner details
    print(f"DEBUG: get_pets called with owner_id={owner_id}")
    query = supabase.table("pets").select("*, owner:users(name, role, avatar_url)")
    
    if owner_id:
        query = query.eq("owner_id", owner_id)
        
    response = query.execute()
    data = response.data
    print(f"DEBUG: Found {len(data) if data else 0} pets")
    
    formatted_data = []
    for item in data:
        # Check if the pet has been adopted
        is_adopted = _check_if_adopted(item.get('id', ''))
        formatted_item = _format_pet(item, is_adopted=is_adopted)
        if formatted_item:
            formatted_data.append(formatted_item)
        
    return formatted_data

@router.get("/{pet_id}", response_model=Pet)
def get_pet(pet_id: str):
    response = supabase.table("pets").select("*, owner:users(name, role, avatar_url)").eq("id", pet_id).single().execute()
    item = response.data
    
    if not item:
        raise HTTPException(status_code=404, detail="Pet not found")
        
    # Check if the pet has been adopted
    is_adopted = _check_if_adopted(pet_id)
    return _format_pet(item, is_adopted=is_adopted)

@router.delete("/{pet_id}")
def delete_pet(pet_id: str):
    # Verify pet exists
    pet_response = supabase.table("pets").select("id").eq("id", pet_id).single().execute()
    if not pet_response.data:
        raise HTTPException(status_code=404, detail="Pet not found")
        
    # Delete pet
    response = supabase.table("pets").delete().eq("id", pet_id).execute()
    
    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=500, detail=str(response.error))
        
    return {"message": "Pet deleted successfully"}