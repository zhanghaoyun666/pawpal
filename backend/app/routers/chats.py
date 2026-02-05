from fastapi import APIRouter, HTTPException
from typing import List
from app.database import supabase
from app.constants import TEST_USER_ID
from app.models.schemas import ChatSession, Message, MessageCreate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chats", tags=["chats"])

# SSE 管理器引用（将在 main.py 中设置）
sse_manager = None


def set_sse_manager(manager):
    """设置 SSE 管理器"""
    global sse_manager
    sse_manager = manager


@router.get("/", response_model=List[ChatSession])
def get_chats(user_id: str = None):
    # Use provided user_id or fallback to TEST_USER_ID
    target_id = user_id if user_id else TEST_USER_ID
    
    # 1. 获取用户拥有的所有宠物ID
    my_pets_res = supabase.table("pets").select("id").eq("owner_id", target_id).execute()
    my_pet_ids = [p['id'] for p in my_pets_res.data]
    
    # 2. 获取用户作为申请人的对话
    user_as_applicant_res = supabase.table("conversations").select("*").eq("user_id", target_id).execute()
    user_as_applicant_convs = user_as_applicant_res.data
    
    # 3. 获取用户作为送养人的对话
    user_as_owner_convs = []
    if my_pet_ids:
        user_as_owner_res = supabase.table("conversations").select("*").in_("pet_id", my_pet_ids).execute()
        user_as_owner_convs = user_as_owner_res.data
    
    # 4. 合并结果并去重
    all_convs = user_as_applicant_convs + user_as_owner_convs
    all_raw_convs = list({c['id']: c for c in all_convs}.values())
    
    if not all_raw_convs:
        return []

    conv_ids = [c['id'] for c in all_raw_convs]

    # Pre-fetch all pet info
    all_pet_ids = list(set([c['pet_id'] for c in all_raw_convs]))
    pets_res = supabase.table("pets").select("id, name, image_url, owner_id").in_("id", all_pet_ids).execute()
    pets_info = {p['id']: p for p in pets_res.data}
    
    # Pre-fetch all unique participant IDs
    all_p_ids = set()
    for c in all_raw_convs:
        all_p_ids.add(c['user_id']) 
        pet_info = pets_info.get(c['pet_id'])
        if pet_info:
            all_p_ids.add(pet_info['owner_id'])
            
    users_res = supabase.table("users").select("id, name, avatar_url, role").in_("id", list(all_p_ids)).execute()
    users_info = {u['id']: u for u in users_res.data}

    # BATCH FETCH LAST MESSAGES
    all_msgs_res = supabase.table("messages")\
        .select("conversation_id, content, created_at, sender_id, read")\
        .in_("conversation_id", conv_ids)\
        .order("created_at", desc=True)\
        .execute()
    
    # Group messages by conversation
    messages_by_conv = {}
    unread_counts = {}
    for m in all_msgs_res.data:
        cid = m['conversation_id']
        if cid not in messages_by_conv:
            messages_by_conv[cid] = m
        
        # Calculate unread count (not from self)
        if m['sender_id'] != target_id and not m['read']:
            unread_counts[cid] = unread_counts.get(cid, 0) + 1

    chats = []
    for item in all_raw_convs:
        pet = pets_info.get(item['pet_id'], {})
        owner_id = pet.get('owner_id')
        applicant_id = item['user_id']
        
        if applicant_id == target_id:
            other_user = users_info.get(owner_id, {})
        else:
            other_user = users_info.get(applicant_id, {})
            
        last_msg = messages_by_conv.get(item['id'])
        unread_count = unread_counts.get(item['id'], 0)
        
        display_name = other_user.get('name', '未知')
        display_image = other_user.get('avatar_url', '') or f"https://api.dicebear.com/7.x/avataaars/svg?seed={display_name}"
        display_role = other_user.get('role', 'user')

        chat = {
            "id": item['id'],
            "petId": item['pet_id'],
            "petName": pet.get('name', 'Unknown'),
            "petImage": pet.get('image_url', ''),
            "coordinatorName": display_name,
            "coordinatorImage": display_image,
            "otherParticipantName": display_name,
            "otherParticipantImage": display_image,
            "otherParticipantRole": 'coordinator' if display_role == 'coordinator' else 'user',
            "lastMessage": last_msg['content'] if last_msg else "暂无消息",
            "lastMessageTime": last_msg['created_at'] if last_msg else item['updated_at'],
            "unreadCount": unread_count
        }
        chats.append(chat)
        
    return chats


@router.get("/{id}/messages", response_model=List[Message])
def get_messages(id: str, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    # 获取对话信息以确定参与者角色
    conv_res = supabase.table("conversations").select("*, pets!inner(*)").eq("id", id).execute()
    if not conv_res.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = conv_res.data[0]
    pet_owner_id = conv['pets']['owner_id']
    applicant_id = conv['user_id']
    
    # 获取消息
    response = supabase.table("messages").select("*").eq("conversation_id", id).order("created_at").execute()
    
    messages = []
    for item in response.data:
        # 更精确地确定发送者角色
        if item['sender_id'] == target_id:
            sender = 'user'
        elif target_id == pet_owner_id:
            sender = 'coordinator'
        else:
            sender = 'coordinator'
            
        messages.append({
            "id": item['id'],
            "sender": sender,
            "text": item['content'],
            "timestamp": item['created_at'],
            "isRead": item['read']
        })
    return messages


@router.put("/{id}/read")
async def mark_as_read(id: str, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    # 获取对话信息
    conv_res = supabase.table("conversations").select("*, pets!inner(*)").eq("id", id).execute()
    if not conv_res.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # 标记消息为已读
    response = supabase.table("messages")\
        .update({"read": True})\
        .eq("conversation_id", id)\
        .neq("sender_id", target_id)\
        .execute()
    
    # 通过 SSE 广播已读状态
    if sse_manager:
        await sse_manager.broadcast_to_chat(id, {
            "type": "messages_read",
            "chat_id": id,
            "user_id": target_id,
            "count": len(response.data) if response.data else 0
        })
        
    return {"status": "success", "updated_count": len(response.data) if response.data else 0}


@router.post("/{id}/messages")
async def send_message(id: str, message: MessageCreate, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    # 获取对话信息
    conv_res = supabase.table("conversations").select("*, pets!inner(*)").eq("id", id).execute()
    if not conv_res.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = conv_res.data[0]
    
    data = {
        "conversation_id": id,
        "sender_id": target_id,
        "content": message.text,
        "read": False
    }
    
    # 保存消息
    response = supabase.table("messages").insert(data).execute()
    
    if response.data:
        message_record = response.data[0]
        
        # 更新对话时间
        supabase.table("conversations").update({
            "updated_at": "now()"
        }).eq("id", id).execute()
        
        # 通过 SSE 广播新消息
        if sse_manager:
            await sse_manager.broadcast_to_chat(id, {
                "type": "new_message",
                "chat_id": id,
                "message": {
                    "id": message_record["id"],
                    "sender_id": target_id,
                    "text": message.text,
                    "timestamp": message_record["created_at"],
                    "isRead": False
                }
            })
            
            # 通知聊天列表更新
            await sse_manager.broadcast_to_chat(id, {
                "type": "chat_updated",
                "chat_id": id
            })
    
    return response.data


@router.delete("/{id}/messages/{message_id}")
def delete_message(id: str, message_id: str, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    response = supabase.table("messages")\
        .delete()\
        .eq("id", message_id)\
        .eq("conversation_id", id)\
        .eq("sender_id", target_id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Message not found or you don't have permission")
    
    return {"status": "success"}


@router.delete("/{id}")
def delete_conversation(id: str, user_id: str = None):
    target_id = user_id if user_id else TEST_USER_ID
    
    # 1. Delete messages first due to FK constraints
    supabase.table("messages").delete().eq("conversation_id", id).execute()
    
    # 2. Delete conversation
    response = supabase.table("conversations").delete().eq("id", id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    return {"status": "success"}
