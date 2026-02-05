import { useState, useCallback, useEffect } from 'react';
import { useSSE } from './useSSE';
import { Message } from '../types';

// SSE 消息类型
interface ChatSSEMessage {
  type: string;
  chat_id?: string;
  message?: {
    id: string;
    sender_id: string;
    text: string;
    timestamp: string;
    isRead: boolean;
  };
  user_id?: string;
  count?: number;
}

interface UseChatSSEOptions {
  userId?: string;
  chatId?: string;
  onNewMessage?: (message: Message) => void;
  onMessagesRead?: (userId: string, count: number) => void;
  onChatUpdated?: (chatId: string) => void;
}

interface UseChatSSEReturn {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  isConnected: boolean;
  subscribe: (chatId: string) => Promise<boolean>;
  unsubscribe: (chatId: string) => Promise<boolean>;
  connect: () => void;
  disconnect: () => void;
}

export const useChatSSE = (options: UseChatSSEOptions): UseChatSSEReturn => {
  const {
    userId,
    chatId,
    onNewMessage,
    onMessagesRead,
    onChatUpdated
  } = options;

  const [subscribedChats, setSubscribedChats] = useState<Set<string>>(new Set());

  // 处理 SSE 消息
  const handleMessage = useCallback((sseMessage: ChatSSEMessage) => {
    const { type } = sseMessage;

    switch (type) {
      case 'new_message':
        if (sseMessage.message && sseMessage.chat_id) {
          const msg: Message = {
            id: sseMessage.message.id,
            sender: 'coordinator', // 需要根据 sender_id 判断
            text: sseMessage.message.text,
            timestamp: sseMessage.message.timestamp,
            isRead: sseMessage.message.isRead
          };
          onNewMessage?.(msg);
        }
        break;

      case 'messages_read':
        if (sseMessage.user_id !== undefined && sseMessage.count !== undefined) {
          onMessagesRead?.(sseMessage.user_id, sseMessage.count);
        }
        break;

      case 'chat_updated':
        if (sseMessage.chat_id) {
          onChatUpdated?.(sseMessage.chat_id);
        }
        break;

      case 'connected':
        console.log('[ChatSSE] 连接成功:', sseMessage.user_id);
        break;

      case 'error':
        console.error('[ChatSSE] 服务器错误:', sseMessage.message);
        break;

      default:
        console.log('[ChatSSE] 收到消息:', type);
    }
  }, [onNewMessage, onMessagesRead, onChatUpdated]);

  // SSE URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const sseUrl = `${baseUrl}/api/sse/connect`;

  // 使用基础 SSE hook
  const { status, lastMessage, connect, disconnect } = useSSE({
    url: sseUrl,
    userId,
    onMessage: handleMessage,
    reconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5
  });

  // 订阅聊天室
  const subscribe = useCallback(async (targetChatId: string): Promise<boolean> => {
    if (!userId) return false;
    
    try {
      const response = await fetch(`${baseUrl}/api/sse/subscribe/${targetChatId}?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setSubscribedChats(prev => new Set([...prev, targetChatId]));
        console.log('[ChatSSE] 已订阅聊天室:', targetChatId);
        return true;
      }
      return false;
    } catch (error) {
      console.error('[ChatSSE] 订阅失败:', error);
      return false;
    }
  }, [userId, baseUrl]);

  // 取消订阅聊天室
  const unsubscribe = useCallback(async (targetChatId: string): Promise<boolean> => {
    if (!userId) return false;
    
    try {
      const response = await fetch(`${baseUrl}/api/sse/unsubscribe/${targetChatId}?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setSubscribedChats(prev => {
          const next = new Set(prev);
          next.delete(targetChatId);
          return next;
        });
        console.log('[ChatSSE] 已取消订阅聊天室:', targetChatId);
        return true;
      }
      return false;
    } catch (error) {
      console.error('[ChatSSE] 取消订阅失败:', error);
      return false;
    }
  }, [userId, baseUrl]);

  // 组件卸载时取消所有订阅
  useEffect(() => {
    return () => {
      subscribedChats.forEach(chatId => {
        unsubscribe(chatId);
      });
    };
  }, [subscribedChats, unsubscribe]);

  return {
    status,
    isConnected: status === 'connected',
    subscribe,
    unsubscribe,
    connect,
    disconnect
  };
};

export default useChatSSE;
