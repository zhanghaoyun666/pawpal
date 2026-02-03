import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import BottomNav from '../components/BottomNav';

const ChatList: React.FC = () => {
  const navigate = useNavigate();
  const { chats, user, refreshChats } = useApp();

  const handleDeleteChat = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (!user || !window.confirm('确定要删除此对话吗？这将同时删除所有聊天频率。')) return;
    try {
      await api.deleteChat(chatId, user.id);
      await refreshChats();
    } catch (error) {
      console.error("Failed to delete chat", error);
    }
  }

  // 添加轮询效果
  useEffect(() => {
    if (user) {
      // 立即刷新一次
      refreshChats().catch(console.error);
      
      // 每10秒刷新一次聊天列表
      const interval = setInterval(() => {
        refreshChats().catch(console.error);
      }, 10000);
      
      return () => clearInterval(interval);
    }
  }, [user, refreshChats]);

  // ... 其余代码保持不变

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden bg-background-light dark:bg-background-dark max-w-md mx-auto pb-24">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm p-4 border-b border-gray-100 dark:border-gray-800">
        <h2 className="text-text-main dark:text-white text-xl font-bold leading-tight tracking-[-0.015em]">消息中心</h2>
        <button className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
          <span className="material-symbols-outlined text-text-main dark:text-white text-2xl">search</span>
        </button>
      </header>

      {/* Chat List */}
      <main className="p-4 flex flex-col gap-4">
        {chats.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-10 text-gray-400">
            <span className="material-symbols-outlined text-5xl mb-2">chat</span>
            <p>暂无消息</p>
          </div>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => navigate(`/chat/${chat.id}`)}
              className="flex items-center gap-4 p-4 bg-card-light dark:bg-card-dark rounded-2xl shadow-sm active:scale-[0.98] transition-transform cursor-pointer relative"
            >
              <div className="relative">
                <div
                  className="w-14 h-14 rounded-full bg-cover bg-center border-2 border-white dark:border-card-dark shadow-sm"
                  style={{ backgroundImage: `url("${chat.otherParticipantImage}")` }}
                ></div>
                <div
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-cover bg-center border-2 border-white dark:border-card-dark"
                  style={{ backgroundImage: `url("${chat.petImage}")` }}
                ></div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline mb-1">
                  <h3 className="font-bold text-text-main dark:text-white truncate pr-2">
                    {chat.otherParticipantName}
                  </h3>
                  <span className="text-xs text-text-muted dark:text-gray-500 whitespace-nowrap">
                    {new Date(chat.lastMessageTime).toLocaleDateString() === new Date().toLocaleDateString()
                      ? new Date(chat.lastMessageTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : new Date(chat.lastMessageTime).toLocaleDateString([], { month: '2-digit', day: '2-digit' })}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <p className={`text-sm truncate pr-2 ${chat.unreadCount > 0 ? 'text-text-main dark:text-white font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>
                    {chat.lastMessage}
                  </p>
                  {chat.unreadCount > 0 && (
                    <div className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-red-500 flex items-center justify-center">
                      <span className="text-[10px] font-bold text-white">{chat.unreadCount}</span>
                    </div>
                  )}
                  <button
                    onClick={(e) => handleDeleteChat(e, chat.id)}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                    title="删除对话"
                  >
                    <span className="material-symbols-outlined text-xl">delete</span>
                  </button>
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