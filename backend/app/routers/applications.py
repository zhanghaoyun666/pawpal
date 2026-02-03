from fastapi import APIRouter, HTTPException
from typing import List
from app.database import supabase
from app.constants import TEST_USER_ID
from app.models.applications_schema import ApplicationCreate, Application

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.post("/", response_model=Application)
def create_application(application: ApplicationCreate):
    # Override user_id with authenticatd user (Test User for MVP)
    app_data = application.model_dump()
    # For now, we still use the hardcoded TEST_USER_ID or the one passed (if we trust it)
    # Ideally, we should use the user_id from the token. 
    # But since the previous code forced TEST_USER_ID, let's check if the frontend sends a valid user_id
    # If frontend sends user_id, use it, otherwise use TEST_USER_ID
    if 'user_id' not in app_data or not app_data['user_id']:
        app_data['user_id'] = TEST_USER_ID
    
    # 1. Create Application
    response = supabase.table("applications").insert(app_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create application")
    
    new_app = response.data[0]
    
    # 2. Auto-Reply Logic
    try:
        print(f"DEBUG: Starting auto-reply for pet_id={app_data['pet_id']}, user_id={app_data['user_id']}")
        # Fetch Pet Owner (Coordinator)
        pet_res = supabase.table("pets").select("owner_id").eq("id", app_data['pet_id']).single().execute()
        if pet_res.data:
            owner_id = pet_res.data['owner_id']
            user_id = app_data['user_id']
            print(f"DEBUG: Found owner_id={owner_id}")
            
            # Check for existing conversation
            # Note: We use .select("*") and then filter, or better yet, just use eq
            conv_res = supabase.table("conversations").select("id")\
                .eq("user_id", user_id)\
                .eq("pet_id", app_data['pet_id'])\
                .execute()
                
            conversation_id = None
            if conv_res.data and len(conv_res.data) > 0:
                conversation_id = conv_res.data[0]['id']
                print(f"DEBUG: Found existing conversation_id={conversation_id}")
            else:
                # Create new conversation
                print("DEBUG: Creating new conversation")
                new_conv = {
                    "user_id": user_id,
                    "pet_id": app_data['pet_id']
                }
                conv_insert = supabase.table("conversations").insert(new_conv).execute()
                if conv_insert.data and len(conv_insert.data) > 0:
                    conversation_id = conv_insert.data[0]['id']
                    print(f"DEBUG: Created new conversation_id={conversation_id}")
            
            # Send Auto-Reply
            if conversation_id:
                print(f"DEBUG: Sending message to conversation_id={conversation_id}")
                
                # 获取申请人信息，使回复更个性化
                user_res = supabase.table("users").select("name").eq("id", user_id).single().execute()
                applicant_name = user_res.data.get('name', '申请人') if user_res.data else '申请人'
                
                # 获取宠物信息
                pet_res = supabase.table("pets").select("name").eq("id", app_data['pet_id']).single().execute()
                pet_name = pet_res.data.get('name', '宠物') if pet_res.data else '宠物'
                
                message = {
                    "conversation_id": conversation_id,
                    "sender_id": owner_id,
                    "content": f"您好{applicant_name}！感谢您对{pet_name}的领养申请。我已经收到了您的申请，会尽快进行审核。请随时通过这里与我沟通，了解更多信息。",
                    "read": False
                }
                supabase.table("messages").insert(message).execute()
                print("DEBUG: Auto-reply message inserted successfully")
                
                # 更新对话时间戳，确保显示在列表顶部
                supabase.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()
                print("DEBUG: Conversation timestamp updated")
            else:
                print("DEBUG: FAILED to get or create conversation_id")
        else:
            print("DEBUG: FAILED to find pet owner")
                
    except Exception as e:
        print(f"Auto-reply failed: {e}")
        import traceback
        traceback.print_exc()
        # Continue even if auto-reply fails, as the application itself was successful
        
    # 3. 实时通知送养人
    try:
        # 获取送养人的所有活跃对话
        owner_conv_res = supabase.table("conversations").select("id, updated_at").eq("user_id", owner_id).execute()
        
        # 更新所有对话的时间戳，确保新申请显示在顶部
        if owner_conv_res.data:
            for conv in owner_conv_res.data:
                supabase.table("conversations").update({"updated_at": "now()"}).eq("id", conv['id']).execute()
        
        print("DEBUG: Owner conversation timestamps updated for real-time notification")
    except Exception as e:
        print(f"DEBUG: Failed to update owner conversation timestamps: {e}")
        
    return new_app

@router.get("/", response_model=List[Application])
def get_my_applications(user_id: str = None, include_approved: bool = True):
    # If user_id is provided, filter by it. Otherwise fallback to TEST_USER_ID or empty.
    target_id = user_id if user_id else TEST_USER_ID
    
    # 1. Fetch applications
    # 默认包含所有申请，包括已批准的
    response = supabase.table("applications").select("*").eq("user_id", target_id).execute()
    apps = response.data
    
    if not apps:
        return []
        
    # 2. Fetch pet details for these applications
    pet_ids = list(set([app['pet_id'] for app in apps if app.get('pet_id')]))
    if pet_ids:
        pets_res = supabase.table("pets").select("id, name, image_url").in_("id", pet_ids).execute()
        pets_dict = {p['id']: p for p in pets_res.data}
        
        # Merge data
        for app in apps:
            pet_data = pets_dict.get(app['pet_id'])
            if pet_data:
                app['pet'] = {
                    "name": pet_data.get('name', '未知'),
                    "image": pet_data.get('image_url', '') or ""
                }
            
    return apps

@router.get("/received", response_model=List[Application])
def get_received_applications(user_id: str = None):
    # Get applications for pets owned by this user (Coordinator)
    target_id = user_id if user_id else TEST_USER_ID
    
    # 1. Get all pet IDs owned by this user
    pets_res = supabase.table("pets").select("id").eq("owner_id", target_id).execute()
    owned_pet_ids = [p['id'] for p in pets_res.data]
    
    if not owned_pet_ids:
        return []
        
    # 2. Get applications for these pets
    response = supabase.table("applications").select("*").in_("pet_id", owned_pet_ids).execute()
    apps = response.data
    
    if not apps:
        return []
        
    # 3. Fetch pet details to include in response
    # We already have some pet info, but let's fetch name and image_url properly
    # Actually we can just use the pets_res result if we select name/image_url there too.
    pets_res_full = supabase.table("pets").select("id, name, image_url").in_("id", owned_pet_ids).execute()
    pets_dict = {p['id']: p for p in pets_res_full.data}
    
    for app in apps:
        pet_data = pets_dict.get(app['pet_id'])
        if pet_data:
            app['pet'] = {
                "name": pet_data.get('name', '未知'),
                "image": pet_data.get('image_url', '') or ""
            }
            
    return apps

@router.put("/{id}/status", response_model=Application)
def update_application_status(id: str, status: str):
    # Validate status
    if status not in ['approved', 'rejected', 'pending']:
         raise HTTPException(status_code=400, detail="Invalid status")
         
    # Update status
    response = supabase.table("applications").update({"status": status}).eq("id", id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Application not found")
        
    updated_app = response.data[0]
    
    return updated_app

@router.delete("/{id}")
def delete_application(id: str, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    # 1. Fetch current application to check status
    app_res = supabase.table("applications").select("*").eq("id", id).execute()
    if not app_res.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application = app_res.data[0]
    
    # Validation: Cannot delete approved applications
    if application['status'] == 'approved':
        raise HTTPException(status_code=400, detail="已完成的领养记录不能删除")
    
    # 2. Cleanup "Health Archives" (Placeholder logic as tables don't exist yet)
    # Theoretically if there were health_records tables, we would delete related rows here.
    # supabase.table("health_records").delete().eq("application_id", id).execute()
    
    # 3. Delete Application
    delete_res = supabase.table("applications").delete().eq("id", id).execute()
    
    if not delete_res.data:
        raise HTTPException(status_code=500, detail="Failed to delete application")
        
    return {"status": "success", "message": "领养记录已删除"}

@router.get("/notifications", response_model=List[dict])
def get_notifications(user_id: str = None):
    """
    获取送养人的实时通知
    """
    target_id = user_id if user_id else TEST_USER_ID
    
    # 获取用户拥有的宠物
    pets_res = supabase.table("pets").select("id, name").eq("owner_id", target_id).execute()
    owned_pet_ids = [p['id'] for p in pets_res.data]
    
    # 获取最近24小时内的申请
    import datetime
    yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
    
    recent_apps_res = supabase.table("applications").select("*")\
        .in_("pet_id", owned_pet_ids)\
        .gte("created_at", yesterday.isoformat())\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    notifications = []
    for app in recent_apps_res.data:
        # 获取申请人信息
        user_res = supabase.table("users").select("name").eq("id", app['user_id']).single().execute()
        applicant_name = user_res.data.get('name', '申请人') if user_res.data else '申请人'
        
        # 获取宠物信息
        pet_info = next((p for p in pets_res.data if p['id'] == app['pet_id']), None)
        pet_name = pet_info.get('name', '宠物') if pet_info else '宠物'
        
        notifications.append({
            "id": app['id'],
            "type": "new_application",
            "title": f"新的领养申请",
            "message": f"{applicant_name}申请领养{pet_name}",
            "created_at": app['created_at'],
            "status": app['status'],
            "pet_id": app['pet_id'],
            "applicant_id": app['user_id']
        })
    
    return notifications