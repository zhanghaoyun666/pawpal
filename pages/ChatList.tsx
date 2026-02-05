import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import BottomNav from '../components/BottomNav';
import { useSSE } from '../hooks/useSSE';

// 格式化时间显示
const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  // 如果是今天，显示时间
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  // 如果是昨天
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天';
  }
  
  // 如果是本周内
  if (days < 7) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    return weekdays[date.getDay()];
  }
  
  // 否则显示日期
  return date.toLocaleDateString([], { month: '2-digit', day: '2-digit' });
};

// 截断消息文本
const truncateMessage = (text: string, maxLength: number = 30): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

const ChatList: React.FC = () => {
  const navigate = useNavigate();
  const { chats, user, refreshChats } = useApp();

  // SSE URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const sseUrl = `${baseUrl}/api/sse/connect`;

  // 处理 SSE 消息
  const handleWsMessage = useCallback((message: any) => {
    // 当收到新消息或聊天更新时刷新列表
    if (message.type === 'new_message' || message.type === 'chat_updated') {
      refreshChats().catch(console.error);
    }
  }, [refreshChats]);

  // 使用 SSE 接收实时通知
  const { status: sseStatus, connect: connectSSE } = useSSE({
    url: sseUrl,
    userId: user?.id,
    onMessage: handleWsMessage,
    reconnect: true,
    reconnectInterval: 5000
  });

  // 连接 SSE
  useEffect(() => {
    if (user) {
      connectSSE();
    }
  }, [user, connectSSE]);

  const handleDeleteChat = async (e: React.MouseEvent, chatId: string, participantName: string) => {
    e.stopPropagation();
    if (!user) return;
    
    if (!window.confirm(`确定要删除与 "${participantName}" 的对话吗？\n\n这将同时删除所有聊天记录，此操作不可恢复。`)) {
      return;
    }
    
    try {
      await api.deleteChat(chatId, user.id);
      await refreshChats();
    } catch (error) {
      console.error("删除对话失败:", error);
      alert('删除对话失败，请稍后重试');
    }
  };

  // 初始加载和轮询（作为后备）
  useEffect(() => {
    if (user) {
      // 立即刷新一次
      refreshChats().catch(console.error);
      
      // 每30秒刷新一次聊天列表（作为 SSE 的后备）
      const interval = setInterval(() => {
        refreshChats().catch(console.error);
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [user, refreshChats]);

  // 渲染连接状态
  const renderConnectionStatus = () => {
    if (sseStatus === 'connected') {
      return (
        <span className="text-[10px] text-green-500 flex items-center gap-0.5">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
          实时
        </span>
      );
    }
    if (sseStatus === 'connecting') {
      return (
        <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
          <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></span>
          连接中
        </span>
      );
    }
    return null;
  };

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden bg-background-light dark:bg-background-dark max-w-md mx-auto pb-24">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm p-4 border-b border-gray-100 dark:border-gray-800">
        <div>
          <h2 className="text-text-main dark:text-white text-xl font-bold leading-tight tracking-[-0.015em]">消息中心</h2>
          {renderConnectionStatus()}
        </div>
        <button 
          onClick={() => alert('搜索功能即将上线')}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
        >
          <span className="material-symbols-outlined text-text-main dark:text-white text-2xl">search</span>
        </button>
      </header>

      {/* Chat List */}
      <main className="p-4 flex flex-col gap-3">
        {chats.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-10 text-gray-400">
            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-4xl">chat</span>
            </div>
            <p className="text-lg font-medium text-gray-500">暂无消息</p>
            <p className="text-sm text-gray-400 mt-2 text-center">
              当您对宠物提交领养申请后，<br/>可以在这里与送养人沟通
            </p>
          </div>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => navigate(`/chat/${chat.id}`)}
              className="flex items-center gap-4 p-4 bg-card-light dark:bg-card-dark rounded-2xl shadow-sm active:scale-[0.98] transition-all cursor-pointer relative group hover:shadow-md"
            >
              {/* 头像区域 */}
              <div className="relative shrink-0">
                <div
                  className="w-14 h-14 rounded-full bg-cover bg-center border-2 border-white dark:border-card-dark shadow-sm"
                  style={{ backgroundImage: `url("${chat.otherParticipantImage}")` }}
                ></div>
                <div
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-cover bg-center border-2 border-white dark:border-card-dark"
                  style={{ backgroundImage: `url("${chat.petImage}")` }}
                ></div>
                {/* 在线状态指示器 */}
                {sseStatus === 'connected' && (
                  <div className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white dark:border-card-dark"></div>
                )}
              </div>

              {/* 内容区域 */}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline mb-1">
                  <h3 className="font-bold text-text-main dark:text-white truncate pr-2">
                    {chat.otherParticipantName}
                    <span className="text-xs font-normal text-gray-400 ml-1">
                      {chat.otherParticipantRole === 'coordinator' ? '(协调员)' : '(申请人)'}
                    </span>
                  </h3>
                  <span className="text-xs text-text-muted dark:text-gray-500 whitespace-nowrap shrink-0">
                    {formatTime(chat.lastMessageTime)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <p className={`text-sm truncate pr-2 ${chat.unreadCount > 0 ? 'text-text-main dark:text-white font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>
                    {chat.lastMessage.startsWith('[图片]') ? (
                      <span className="flex items-center gap-1">
                        <span className="material-symbols-outlined text-base">image</span>
                        图片
                      </span>
                    ) : (
                      truncateMessage(chat.lastMessage)
                    )}
                  </p>
                  
                  <div className="flex items-center gap-1 shrink-0">
                    {chat.unreadCount > 0 && (
                      <div className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-red-500 flex items-center justify-center">
                        <span className="text-[10px] font-bold text-white">{chat.unreadCount > 99 ? '99+' : chat.unreadCount}</span>
                      </div>
                    )}
                    <button
                      onClick={(e) => handleDeleteChat(e, chat.id, chat.otherParticipantName)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all opacity-0 group-hover:opacity-100"
                      title="删除对话"
                    >
                      <span className="material-symbols-outlined text-lg">delete</span>
                    </button>
                  </div>
                </div>
                
                {/* 宠物标签 */}
                <div className="mt-1.5 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[12px] text-gray-400">pets</span>
                  <span className="text-xs text-gray-400 truncate">{chat.petName}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </main>

      <BottomNav />
    </div>
  );
};

export default ChatList;
