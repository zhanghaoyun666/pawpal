import { useState, useEffect, useRef, useCallback } from 'react';

// SSE 连接状态
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// SSE 消息类型
interface SSEMessage {
  type: string;
  [key: string]: any;
}

// SSE 配置选项
interface UseSSEOptions {
  url: string;
  userId?: string;
  onMessage?: (message: SSEMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseSSEReturn {
  status: ConnectionStatus;
  lastMessage: SSEMessage | null;
  connect: () => void;
  disconnect: () => void;
}

export const useSSE = (options: UseSSEOptions): UseSSEReturn => {
  const {
    url,
    userId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<SSEMessage | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef(false);

  // 构建 SSE URL
  const buildUrl = useCallback(() => {
    const sseUrl = new URL(url);
    if (userId) {
      sseUrl.searchParams.append('user_id', userId);
    }
    return sseUrl.toString();
  }, [url, userId]);

  // 断开连接
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    setStatus('disconnected');
    onDisconnect?.();
  }, [onDisconnect]);

  // 连接 SSE
  const connect = useCallback(() => {
    if (eventSourceRef.current?.readyState === EventSource.OPEN) {
      console.log('[SSE] 已经连接');
      return;
    }

    // 清理之前的连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    isManualDisconnectRef.current = false;
    setStatus('connecting');

    try {
      const sseUrl = buildUrl();
      console.log('[SSE] 正在连接:', sseUrl);
      
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        console.log('[SSE] 连接成功');
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[SSE] 收到消息:', data);
          
          // 处理心跳
          if (data.type === 'heartbeat') {
            return;
          }
          
          setLastMessage(data);
          onMessage?.(data);
        } catch (error) {
          console.error('[SSE] 解析消息失败:', error);
        }
      };

      es.onerror = (error) => {
        console.error('[SSE] 连接错误:', error);
        setStatus('error');
        onError?.(error);
        
        // 关闭当前连接
        es.close();
        eventSourceRef.current = null;
        
        // 自动重连
        if (reconnect && !isManualDisconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`[SSE] ${reconnectInterval}ms 后尝试第 ${reconnectAttemptsRef.current} 次重连`);
          
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

    } catch (error) {
      console.error('[SSE] 创建连接失败:', error);
      setStatus('error');
    }
  }, [buildUrl, reconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onError, onMessage]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    lastMessage,
    connect,
    disconnect
  };
};

export default useSSE;
