import { useState, useCallback, useEffect, useRef } from 'react';
import { Message } from '../types';
import { api } from '../services/api';

interface UseChatPollingOptions {
  chatId?: string;
  userId?: string;
  enabled?: boolean;
  onNewMessages?: (messages: Message[]) => void;
}

interface UseChatPollingReturn {
  isPolling: boolean;
  lastPollTime: Date | null;
  error: string | null;
  startPolling: () => void;
  stopPolling: () => void;
  pollNow: () => Promise<void>;
}

export const useChatPolling = (options: UseChatPollingOptions): UseChatPollingReturn => {
  const { chatId, userId, enabled = true, onNewMessages } = options;
  
  const [isPolling, setIsPolling] = useState(false);
  const [lastPollTime, setLastPollTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastMessageIdsRef = useRef<Set<string>>(new Set());
  const isFirstPollRef = useRef(true);

  // 执行一次轮询
  const pollNow = useCallback(async () => {
    if (!chatId || !userId) return;
    
    try {
      setError(null);
      const messages = await api.getMessages(chatId, userId);
      
      // 第一次轮询：记录所有消息ID，不触发回调
      if (isFirstPollRef.current) {
        lastMessageIdsRef.current = new Set(messages.map(m => m.id));
        isFirstPollRef.current = false;
        setLastPollTime(new Date());
        return;
      }
      
      // 找出新消息
      const currentIds = new Set(messages.map(m => m.id));
      const newMessages = messages.filter(m => !lastMessageIdsRef.current.has(m.id));
      
      if (newMessages.length > 0) {
        console.log(`[Polling] 发现 ${newMessages.length} 条新消息`);
        onNewMessages?.(newMessages);
      }
      
      lastMessageIdsRef.current = currentIds;
      setLastPollTime(new Date());
    } catch (err) {
      console.error('[Polling] 轮询失败:', err);
      setError('获取消息失败');
    }
  }, [chatId, userId, onNewMessages]);

  // 开始轮询
  const startPolling = useCallback(() => {
    if (intervalRef.current || !enabled) return;
    
    console.log('[Polling] 开始轮询，间隔 3 秒');
    setIsPolling(true);
    isFirstPollRef.current = true;
    
    // 立即执行一次
    pollNow();
    
    // 设置定时轮询
    intervalRef.current = setInterval(() => {
      pollNow();
    }, 3000); // 每 3 秒轮询一次
  }, [enabled, pollNow]);

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
    console.log('[Polling] 停止轮询');
  }, []);

  // 当 chatId 或 userId 变化时，重置并重新开始
  useEffect(() => {
    if (chatId && userId && enabled) {
      isFirstPollRef.current = true;
      lastMessageIdsRef.current = new Set();
      startPolling();
    } else {
      stopPolling();
    }
    
    return () => {
      stopPolling();
    };
  }, [chatId, userId, enabled, startPolling, stopPolling]);

  return {
    isPolling,
    lastPollTime,
    error,
    startPolling,
    stopPolling,
    pollNow
  };
};

export default useChatPolling;
