"""
WebSocket 路由
处理实时聊天连接
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging
from app.websocket import manager
from app.database import supabase
from app.auth_utils import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket 连接端点
    
    连接参数:
    - token: JWT 认证令牌（可选，如果提供则进行认证）
    - user_id: 用户ID（可选，用于简单身份验证）
    
    消息格式:
    - 加入聊天室: {"type": "join", "chat_id": "xxx"}
    - 发送消息: {"type": "message", "chat_id": "xxx", "text": "消息内容"}
    - 离开聊天室: {"type": "leave", "chat_id": "xxx"}
    - 已读回执: {"type": "read", "chat_id": "xxx"}
    - 心跳: {"type": "ping"}
    """
    
    # 验证用户身份
    authenticated_user_id = None
    
    if token:
        try:
            payload = verify_token(token)
            authenticated_user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"Token 验证失败: {e}")
    
    # 如果没有 token 或验证失败，使用 user_id 参数（开发环境）
    if not authenticated_user_id and user_id:
        authenticated_user_id = user_id
    
    if not authenticated_user_id:
        await websocket.close(code=4001, reason="未提供有效的认证信息")
        return
    
    # 接受连接
    await manager.connect(websocket, authenticated_user_id)
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "user_id": authenticated_user_id,
            "message": "WebSocket 连接成功"
        })
        
        # 通知用户上线（可选）
        await manager.send_to_user(authenticated_user_id, {
            "type": "system",
            "message": "您已连接到实时聊天服务器"
        })
        
        while True:
            # 接收消息
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                chat_id = message_data.get("chat_id")
                
                # 处理心跳
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                
                # 处理加入聊天室
                if message_type == "join":
                    if not chat_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": "缺少 chat_id 参数"
                        })
                        continue
                    
                    # 验证用户是否属于该聊天室
                    if await verify_chat_participant(chat_id, authenticated_user_id):
                        manager.join_chat(websocket, chat_id)
                        await websocket.send_json({
                            "type": "joined",
                            "chat_id": chat_id
                        })
                        
                        # 通知其他用户有人加入（可选）
                        await manager.broadcast_to_chat(chat_id, {
                            "type": "user_joined",
                            "user_id": authenticated_user_id,
                            "chat_id": chat_id
                        }, exclude_user_id=authenticated_user_id)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "您没有权限加入该聊天室"
                        })
                
                # 处理发送消息
                elif message_type == "message":
                    text = message_data.get("text")
                    if not chat_id or not text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "缺少 chat_id 或 text 参数"
                        })
                        continue
                    
                    # 验证用户是否属于该聊天室
                    if not await verify_chat_participant(chat_id, authenticated_user_id):
                        await websocket.send_json({
                            "type": "error",
                            "message": "您没有权限在该聊天室发送消息"
                        })
                        continue
                    
                    # 保存消息到数据库
                    try:
                        result = supabase.table("messages").insert({
                            "conversation_id": chat_id,
                            "sender_id": authenticated_user_id,
                            "content": text,
                            "read": False
                        }).execute()
                        
                        if result.data:
                            message_record = result.data[0]
                            
                            # 更新对话的更新时间
                            supabase.table("conversations").update({
                                "updated_at": "now()"
                            }).eq("id", chat_id).execute()
                            
                            # 广播消息给聊天室所有人
                            await manager.broadcast_to_chat(chat_id, {
                                "type": "new_message",
                                "chat_id": chat_id,
                                "message": {
                                    "id": message_record["id"],
                                    "sender_id": authenticated_user_id,
                                    "text": text,
                                    "timestamp": message_record["created_at"],
                                    "isRead": False
                                }
                            })
                            
                            # 发送确认给发送者
                            await websocket.send_json({
                                "type": "message_sent",
                                "chat_id": chat_id,
                                "message_id": message_record["id"],
                                "timestamp": message_record["created_at"]
                            })
                            
                            logger.info(f"用户 {authenticated_user_id} 在聊天室 {chat_id} 发送消息")
                    
                    except Exception as e:
                        logger.error(f"保存消息失败: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "发送消息失败，请重试"
                        })
                
                # 处理已读回执
                elif message_type == "read":
                    if not chat_id:
                        continue
                    
                    try:
                        # 标记消息为已读
                        result = supabase.table("messages").update({
                            "read": True
                        }).eq("conversation_id", chat_id).neq("sender_id", authenticated_user_id).execute()
                        
                        # 广播已读状态
                        await manager.broadcast_to_chat(chat_id, {
                            "type": "messages_read",
                            "chat_id": chat_id,
                            "user_id": authenticated_user_id,
                            "count": len(result.data) if result.data else 0
                        })
                        
                        logger.info(f"用户 {authenticated_user_id} 标记聊天室 {chat_id} 消息为已读")
                    
                    except Exception as e:
                        logger.error(f"标记已读失败: {e}")
                
                # 处理离开聊天室
                elif message_type == "leave":
                    if chat_id:
                        manager.leave_chat(websocket, chat_id)
                        await websocket.send_json({
                            "type": "left",
                            "chat_id": chat_id
                        })
                        
                        # 通知其他用户有人离开（可选）
                        await manager.broadcast_to_chat(chat_id, {
                            "type": "user_left",
                            "user_id": authenticated_user_id,
                            "chat_id": chat_id
                        }, exclude_user_id=authenticated_user_id)
                
                # 处理打字状态
                elif message_type == "typing":
                    if chat_id:
                        await manager.broadcast_to_chat(chat_id, {
                            "type": "typing",
                            "chat_id": chat_id,
                            "user_id": authenticated_user_id
                        }, exclude_user_id=authenticated_user_id)
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"未知的消息类型: {message_type}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的 JSON 格式"
                })
            
            except Exception as e:
                logger.error(f"处理 WebSocket 消息时出错: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "处理消息时出错"
                })
    
    except WebSocketDisconnect:
        logger.info(f"用户 {authenticated_user_id} WebSocket 断开连接")
    
    finally:
        manager.disconnect(websocket)


async def verify_chat_participant(chat_id: str, user_id: str) -> bool:
    """
    验证用户是否是聊天室的参与者
    """
    try:
        # 获取对话信息
        conv_res = supabase.table("conversations").select("*, pets!inner(*)").eq("id", chat_id).execute()
        
        if not conv_res.data:
            return False
        
        conv = conv_res.data[0]
        
        # 检查用户是否是申请人
        if conv["user_id"] == user_id:
            return True
        
        # 检查用户是否是宠物主人
        if conv["pets"]["owner_id"] == user_id:
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"验证聊天室参与者失败: {e}")
        return False


@router.get("/ws/online-users")
async def get_online_users():
    """获取当前在线用户列表（管理用途）"""
    return {
        "online_users": manager.get_online_users(),
        "count": len(manager.get_online_users())
    }
