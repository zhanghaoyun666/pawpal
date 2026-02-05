import { useState, useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { Message, MessageStatus } from '../types';

// WebSocket 消息类型
interface ChatWebSocketMessage {
  type: string;
  chat_id?: string;
  message?: WebSocketMessageData;
  user_id?: string;
  count?: number;
  message_id?: string;
  timestamp?: string;
}

interface WebSocketMessageData {
  id: string;
  sender_id: string;
  text: string;
  timestamp: string;
  isRead: boolean;
}

interface UseChatWebSocketOptions {
  userId?: string;
  token?: string;
  chatId?: string;
  onNewMessage?: (message: Message) => void;
  onMessagesRead?: (userId: string, count: number) => void;
  onUserJoined?: (userId: string) => void;
  onUserLeft?: (userId: string) => void;
  onTyping?: (userId: string) => void;
}

interface UseChatWebSocketReturn {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  isConnected: boolean;
  joinChat: (chatId: string) => boolean;
  leaveChat: (chatId: string) => boolean;
  sendMessage: (chatId: string, text: string) => boolean;
  sendReadReceipt: (chatId: string) => boolean;
  sendTyping: (chatId: string) => boolean;
  connect: () => void;
  disconnect: () => void;
}

export const useChatWebSocket = (options: UseChatWebSocketOptions): UseChatWebSocketReturn => {
  const {
    userId,
    token,
    chatId,
    onNewMessage,
    onMessagesRead,
    onUserJoined,
    onUserLeft,
    onTyping
  } = options;

  const [joinedChats, setJoinedChats] = useState<Set<string>>(new Set());

  // 处理 WebSocket 消息
  const handleMessage = useCallback((wsMessage: ChatWebSocketMessage) => {
    const { type } = wsMessage;

    switch (type) {
      case 'new_message':
        if (wsMessage.message && wsMessage.chat_id) {
          const msg: Message = {
            id: wsMessage.message.id,
            sender: 'coordinator', // 需要根据 sender_id 判断
            text: wsMessage.message.text,
            timestamp: wsMessage.message.timestamp || new Date().toISOString(),
            isRead: wsMessage.message.isRead,
            status: 'sent'
          };
          onNewMessage?.(msg);
        }
        break;

      case 'messages_read':
        if (wsMessage.user_id !== undefined && wsMessage.count !== undefined) {
          onMessagesRead?.(wsMessage.user_id, wsMessage.count);
        }
        break;

      case 'user_joined':
        if (wsMessage.user_id) {
          onUserJoined?.(wsMessage.user_id);
        }
        break;

      case 'user_left':
        if (wsMessage.user_id) {
          onUserLeft?.(wsMessage.user_id);
        }
        break;

      case 'typing':
        if (wsMessage.user_id) {
          onTyping?.(wsMessage.user_id);
        }
        break;

      case 'message_sent':
        // 消息发送成功的确认
        console.log('[ChatWebSocket] 消息发送成功:', wsMessage.message_id);
        break;

      case 'error':
        console.error('[ChatWebSocket] 服务器错误:', wsMessage.message);
        break;

      case 'connected':
        console.log('[ChatWebSocket] 连接成功，用户ID:', wsMessage.user_id);
        break;

      case 'joined':
        if (wsMessage.chat_id) {
          setJoinedChats(prev => new Set([...prev, wsMessage.chat_id!]));
          console.log('[ChatWebSocket] 已加入聊天室:', wsMessage.chat_id);
        }
        break;

      case 'left':
        if (wsMessage.chat_id) {
          setJoinedChats(prev => {
            const next = new Set(prev);
            next.delete(wsMessage.chat_id!);
            return next;
          });
          console.log('[ChatWebSocket] 已离开聊天室:', wsMessage.chat_id);
        }
        break;

      default:
        console.log('[ChatWebSocket] 未知消息类型:', type);
    }
  }, [onNewMessage, onMessagesRead, onUserJoined, onUserLeft, onTyping]);

  // WebSocket URL
  const wsUrl = import.meta.env.VITE_WS_URL || 
    (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace('http', 'ws') + '/ws/chat';

  // 使用基础 WebSocket hook
  const { status, sendMessage: sendWsMessage, connect, disconnect } = useWebSocket({
    url: wsUrl,
    userId,
    token,
    onMessage: handleMessage,
    reconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000
  });

  // 加入聊天室
  const joinChat = useCallback((targetChatId: string): boolean => {
    if (joinedChats.has(targetChatId)) {
      console.log('[ChatWebSocket] 已经在聊天室中:', targetChatId);
      return true;
    }
    
    return sendWsMessage({
      type: 'join',
      chat_id: targetChatId
    });
  }, [sendWsMessage, joinedChats]);

  // 离开聊天室
  const leaveChat = useCallback((targetChatId: string): boolean => {
    const success = sendWsMessage({
      type: 'leave',
      chat_id: targetChatId
    });
    
    if (success) {
      setJoinedChats(prev => {
        const next = new Set(prev);
        next.delete(targetChatId);
        return next;
      });
    }
    
    return success;
  }, [sendWsMessage]);

  // 发送消息
  const sendMessage = useCallback((targetChatId: string, text: string): boolean => {
    return sendWsMessage({
      type: 'message',
      chat_id: targetChatId,
      text
    });
  }, [sendWsMessage]);

  // 发送已读回执
  const sendReadReceipt = useCallback((targetChatId: string): boolean => {
    return sendWsMessage({
      type: 'read',
      chat_id: targetChatId
    });
  }, [sendWsMessage]);

  // 发送正在输入状态
  const sendTyping = useCallback((targetChatId: string): boolean => {
    return sendWsMessage({
      type: 'typing',
      chat_id: targetChatId
    });
  }, [sendWsMessage]);

  // 组件卸载时离开所有聊天室
  useEffect(() => {
    return () => {
      joinedChats.forEach(chatId => {
        leaveChat(chatId);
      });
    };
  }, [joinedChats, leaveChat]);

  return {
    status,
    isConnected: status === 'connected',
    joinChat,
    leaveChat,
    sendMessage,
    sendReadReceipt,
    sendTyping,
    connect,
    disconnect
  };
};

export default useChatWebSocket;
