"""
Server-Sent Events (SSE) 路由
用于 Vercel 等不支持 WebSocket 的环境
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Set
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sse", tags=["sse"])

# 存储客户端连接
# user_id -> Queue
clients: Dict[str, asyncio.Queue] = {}

# 用户订阅的聊天室
# user_id -> Set[chat_id]
user_chats: Dict[str, Set[str]] = {}


class SSEManager:
    """SSE 连接管理器"""
    
    @staticmethod
    def connect(user_id: str) -> asyncio.Queue:
        """建立 SSE 连接"""
        queue = asyncio.Queue()
        clients[user_id] = queue
        user_chats[user_id] = set()
        logger.info(f"SSE 用户 {user_id} 已连接，当前在线: {len(clients)}")
        return queue
    
    @staticmethod
    def disconnect(user_id: str):
        """断开 SSE 连接"""
        if user_id in clients:
            del clients[user_id]
        if user_id in user_chats:
            del user_chats[user_id]
        logger.info(f"SSE 用户 {user_id} 已断开，当前在线: {len(clients)}")
    
    @staticmethod
    def subscribe(user_id: str, chat_id: str):
        """订阅聊天室"""
        if user_id in user_chats:
            user_chats[user_id].add(chat_id)
            logger.info(f"用户 {user_id} 订阅聊天室 {chat_id}")
    
    @staticmethod
    def unsubscribe(user_id: str, chat_id: str):
        """取消订阅聊天室"""
        if user_id in user_chats:
            user_chats[user_id].discard(chat_id)
            logger.info(f"用户 {user_id} 取消订阅聊天室 {chat_id}")
    
    @staticmethod
    async def send_to_user(user_id: str, data: dict):
        """向指定用户发送消息"""
        if user_id in clients:
            try:
                await clients[user_id].put(data)
            except Exception as e:
                logger.error(f"向用户 {user_id} 发送消息失败: {e}")
    
    @staticmethod
    async def broadcast_to_chat(chat_id: str, data: dict, exclude_user_id: Optional[str] = None):
        """向聊天室广播消息"""
        for user_id, chats in user_chats.items():
            if chat_id in chats:
                if exclude_user_id and user_id == exclude_user_id:
                    continue
                await SSEManager.send_to_user(user_id, data)
    
    @staticmethod
    def is_user_online(user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in clients


# 创建管理器实例
sse_manager = SSEManager()


async def event_generator(user_id: str, request: Request):
    """SSE 事件生成器"""
    queue = sse_manager.connect(user_id)
    
    try:
        # 发送初始连接成功事件
        yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id, 'time': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
        
        while True:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                break
            
            try:
                # 等待消息，设置超时以便定期检查连接状态
                data = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield f"data: {json.dumps({'type': 'heartbeat', 'time': datetime.now().isoformat()})}\n\n"
    
    except Exception as e:
        logger.error(f"SSE 事件生成器错误: {e}")
    
    finally:
        sse_manager.disconnect(user_id)


@router.get("/connect")
async def sse_connect(
    request: Request,
    user_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """
    SSE 连接端点
    
    使用方式:
    const eventSource = new EventSource('/api/sse/connect?user_id=xxx');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    """
    if not user_id:
        return {"error": "缺少 user_id 参数"}
    
    return StreamingResponse(
        event_generator(user_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.post("/subscribe/{chat_id}")
async def subscribe_chat(chat_id: str, user_id: Optional[str] = Query(None)):
    """订阅聊天室消息"""
    if not user_id:
        return {"error": "缺少 user_id 参数"}
    
    sse_manager.subscribe(user_id, chat_id)
    return {"status": "success", "message": f"已订阅聊天室 {chat_id}"}


@router.post("/unsubscribe/{chat_id}")
async def unsubscribe_chat(chat_id: str, user_id: Optional[str] = Query(None)):
    """取消订阅聊天室"""
    if not user_id:
        return {"error": "缺少 user_id 参数"}
    
    sse_manager.unsubscribe(user_id, chat_id)
    return {"status": "success", "message": f"已取消订阅聊天室 {chat_id}"}


@router.get("/online-users")
async def get_online_users():
    """获取在线用户列表"""
    return {
        "online_users": list(clients.keys()),
        "count": len(clients),
        "subscriptions": {uid: list(chats) for uid, chats in user_chats.items()}
    }


# 导出管理器供其他模块使用
__all__ = ['sse_manager', 'router']
