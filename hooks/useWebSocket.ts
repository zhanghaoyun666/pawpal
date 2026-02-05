import { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket 连接状态
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// WebSocket 消息类型
interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// WebSocket 配置选项
interface UseWebSocketOptions {
  url: string;
  userId?: string;
  token?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  sendMessage: (message: object) => boolean;
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
}

export const useWebSocket = (options: UseWebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    userId,
    token,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef(false);

  // 构建 WebSocket URL
  const buildUrl = useCallback(() => {
    const wsUrl = new URL(url);
    if (token) {
      wsUrl.searchParams.append('token', token);
    }
    if (userId) {
      wsUrl.searchParams.append('user_id', userId);
    }
    return wsUrl.toString();
  }, [url, token, userId]);

  // 发送心跳
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // 开始心跳
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval > 0) {
      heartbeatTimerRef.current = setInterval(sendHeartbeat, heartbeatInterval);
    }
  }, [heartbeatInterval, sendHeartbeat]);

  // 停止心跳
  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // 连接 WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] 已经连接');
      return;
    }

    isManualDisconnectRef.current = false;
    setStatus('connecting');

    try {
      const wsUrl = buildUrl();
      console.log('[WebSocket] 正在连接:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] 连接成功');
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[WebSocket] 收到消息:', message);
          
          // 处理心跳响应
          if (message.type === 'pong') {
            return;
          }
          
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('[WebSocket] 解析消息失败:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] 连接关闭:', event.code, event.reason);
        setStatus('disconnected');
        stopHeartbeat();
        onDisconnect?.();

        // 自动重连
        if (reconnect && !isManualDisconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`[WebSocket] ${reconnectInterval}ms 后尝试第 ${reconnectAttemptsRef.current} 次重连`);
          
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', error);
        setStatus('error');
        onError?.(error);
      };

    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error);
      setStatus('error');
    }
  }, [buildUrl, reconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onError, onMessage, startHeartbeat, stopHeartbeat]);

  // 断开连接
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    stopHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setStatus('disconnected');
  }, [stopHeartbeat]);

  // 发送消息
  const sendMessage = useCallback((message: object): boolean => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('[WebSocket] 发送消息失败:', error);
        return false;
      }
    }
    console.warn('[WebSocket] 连接未建立，无法发送消息');
    return false;
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    sendMessage,
    lastMessage,
    connect,
    disconnect
  };
};

export default useWebSocket;
