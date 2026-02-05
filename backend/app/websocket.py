"""
WebSocket 连接管理器
管理所有 WebSocket 连接，支持按用户ID和聊天室ID分组
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 用户ID -> WebSocket 连接列表（一个用户可能有多个连接，如多设备登录）
        self.user_connections: Dict[str, List[WebSocket]] = {}
        # 聊天室ID -> 用户ID 集合
        self.chat_rooms: Dict[str, Set[str]] = {}
        # WebSocket -> 用户信息映射
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        
        # 记录连接信息
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        
        self.connection_info[websocket] = {
            "user_id": user_id,
            "chat_rooms": set()
        }
        
        logger.info(f"用户 {user_id} 已连接，当前连接数: {len(self.user_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        if websocket not in self.connection_info:
            return
        
        info = self.connection_info[websocket]
        user_id = info["user_id"]
        
        # 从所有聊天室中移除
        for chat_id in info["chat_rooms"]:
            if chat_id in self.chat_rooms:
                self.chat_rooms[chat_id].discard(user_id)
                if not self.chat_rooms[chat_id]:
                    del self.chat_rooms[chat_id]
        
        # 从用户连接列表中移除
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 删除连接信息
        del self.connection_info[websocket]
        
        logger.info(f"用户 {user_id} 已断开连接")
    
    def join_chat(self, websocket: WebSocket, chat_id: str):
        """将连接加入指定聊天室"""
        if websocket not in self.connection_info:
            return
        
        info = self.connection_info[websocket]
        user_id = info["user_id"]
        
        # 添加到聊天室
        if chat_id not in self.chat_rooms:
            self.chat_rooms[chat_id] = set()
        self.chat_rooms[chat_id].add(user_id)
        
        # 记录用户加入的聊天室
        info["chat_rooms"].add(chat_id)
        
        logger.info(f"用户 {user_id} 加入聊天室 {chat_id}")
    
    def leave_chat(self, websocket: WebSocket, chat_id: str):
        """将连接从指定聊天室移除"""
        if websocket not in self.connection_info:
            return
        
        info = self.connection_info[websocket]
        user_id = info["user_id"]
        
        # 从聊天室移除
        if chat_id in self.chat_rooms:
            self.chat_rooms[chat_id].discard(user_id)
            if not self.chat_rooms[chat_id]:
                del self.chat_rooms[chat_id]
        
        # 从用户记录中移除
        info["chat_rooms"].discard(chat_id)
        
        logger.info(f"用户 {user_id} 离开聊天室 {chat_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """向指定用户的所有连接发送消息"""
        if user_id not in self.user_connections:
            return
        
        json_message = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(json_message)
            except Exception as e:
                logger.error(f"发送消息给用户 {user_id} 失败: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_chat(self, chat_id: str, message: dict, exclude_user_id: str = None):
        """向聊天室的所有在线用户广播消息"""
        if chat_id not in self.chat_rooms:
            return
        
        json_message = json.dumps(message, ensure_ascii=False)
        
        for user_id in self.chat_rooms[chat_id]:
            # 可以选择排除某个用户（如发送者）
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            if user_id in self.user_connections:
                disconnected = []
                for websocket in self.user_connections[user_id]:
                    try:
                        await websocket.send_text(json_message)
                    except Exception as e:
                        logger.error(f"广播消息给用户 {user_id} 失败: {e}")
                        disconnected.append(websocket)
                
                # 清理断开的连接
                for websocket in disconnected:
                    self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """向所有在线用户广播消息"""
        json_message = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        for websocket in self.connection_info:
            try:
                await websocket.send_text(json_message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_online_users(self) -> List[str]:
        """获取所有在线用户ID列表"""
        return list(self.user_connections.keys())
    
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0


# 全局连接管理器实例
manager = ConnectionManager()
