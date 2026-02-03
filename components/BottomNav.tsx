import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

const BottomNav: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { chats, user, receivedApplications } = useApp();

  const totalUnreadCount = chats.reduce((acc, chat) => acc + (chat.unreadCount || 0), 0);
  const hasNewApplications = user?.role === 'coordinator' && receivedApplications.some(app => app.status === 'pending');
  const isActive = (path: string) => location.pathname === path || (path !== '/' && location.pathname.startsWith(path));

  return (
    <nav className="fixed bottom-0 w-full max-w-md mx-auto bg-card-light dark:bg-card-dark border-t border-gray-100 dark:border-gray-800 px-8 py-3 flex justify-between items-center z-20 rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.02)] left-0 right-0">
      <button
        onClick={() => navigate('/')}
        className={`flex flex-col items-center gap-1 transition-colors ${location.pathname === '/' ? 'text-secondary dark:text-primary' : 'text-gray-400 dark:text-gray-500 hover:text-secondary dark:hover:text-primary'}`}
      >
        <span className={`material-symbols-outlined text-2xl ${location.pathname === '/' ? 'filled' : ''}`}>home</span>
        <span className="text-[10px] font-bold">首页</span>
      </button>

      <button
        onClick={() => navigate('/favorites')}
        className={`flex flex-col items-center gap-1 transition-colors ${isActive('/favorites') ? 'text-secondary dark:text-primary' : 'text-gray-400 dark:text-gray-500 hover:text-secondary dark:hover:text-primary'}`}
      >
        <span className={`material-symbols-outlined text-2xl ${isActive('/favorites') ? 'filled' : ''}`}>favorite</span>
        <span className="text-[10px] font-medium">收藏</span>
      </button>

      <button
        onClick={() => navigate('/chat')}
        className={`flex flex-col items-center gap-1 transition-colors relative ${isActive('/chat') ? 'text-secondary dark:text-primary' : 'text-gray-400 dark:text-gray-500 hover:text-secondary dark:hover:text-primary'}`}
      >
        <div className="relative">
          <span className={`material-symbols-outlined text-2xl ${isActive('/chat') ? 'filled' : ''}`}>chat_bubble</span>
          {totalUnreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border border-white dark:border-card-dark"></span>
            </span>
          )}
        </div>
        <span className="text-[10px] font-medium">消息</span>
      </button>

      <button
        onClick={() => navigate('/profile')}
        className={`flex flex-col items-center gap-1 transition-colors relative ${isActive('/profile') ? 'text-secondary dark:text-primary' : 'text-gray-400 dark:text-gray-500 hover:text-secondary dark:hover:text-primary'}`}
      >
        <div className="relative">
          <span className={`material-symbols-outlined text-2xl ${isActive('/profile') ? 'filled' : ''}`}>person</span>
          {hasNewApplications && (
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border border-white dark:border-card-dark"></span>
            </span>
          )}
        </div>
        <span className="text-[10px] font-medium">我的</span>
      </button>
    </nav>
  );
};

export default BottomNav;