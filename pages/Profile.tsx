import React from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const Profile: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, applications, receivedApplications } = useApp();






  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden bg-background-light dark:bg-background-dark max-w-md mx-auto">
      {/* ... Header & User Info ... */}

      {/* ... (Keep Header and User Info sections same as before) ... */}
      {/* Since replace_file_content replaces a block, I need to be careful not to delete the header/info unless I include them. 
         But I can just target the specific areas. 
         Wait, splitting this into smaller chunks is safer.
      */}
      {/* Header */}
      <div className="flex items-center px-4 py-4 justify-between sticky top-0 z-10 bg-background-light dark:bg-background-dark">
        <div className="size-12"></div>
        <h2 className="text-text-main dark:text-white text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center">个人中心</h2>
        <div className="flex size-12 items-center justify-end">
          <button className="flex items-center justify-center rounded-full text-text-main dark:text-white p-0">
            <span className="material-symbols-outlined text-2xl">settings</span>
          </button>
        </div>
      </div>

      <div className="flex px-4 pt-2 pb-6 flex-col items-center">
        {user ? (
          <>
            <div className="relative group">
              <div
                className="bg-center bg-no-repeat bg-cover rounded-full h-32 w-32 shadow-sm border-4 border-white dark:border-card-dark"
                style={{ backgroundImage: `url("${user.avatar_url || 'https://lh3.googleusercontent.com/aida-public/AB6AXuCUnwZJX7c_IH8u_UKZLr2c3c93M-Sh8N5Ingljqn1hTU5RY9m01w0JDw3gdPKXmOmTlhcNo_aP56KEx4H81l7eAPg3ggWlmpfOlHsi5tPoCFF0H1Y6rastFx7GLD7IZq8zy6DKD5Vfc9l9hF4f8KBKTzmgCOYFAxpV9kEV7OvelmExh_H8IXjuUBgTgVIs4MuG8_WDm46wLt45KP8qvkSzqviKWd7V9jHicFA4TzIuKnRCYO6aWj1pCCfwf1hnY5ewaql-VxRb-Fo'}")` }}
              ></div>
              <div className="absolute bottom-1 right-1 bg-primary text-white p-1.5 rounded-full border-[3px] border-background-light dark:border-background-dark flex items-center justify-center">
                <span className="material-symbols-outlined text-sm">edit</span>
              </div>
            </div>
            <div className="flex flex-col items-center justify-center mt-4">
              <p className="text-text-main dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em] text-center">{user.name || user.email}</p>
              <p className="text-[#97794e] dark:text-[#eba747] text-sm font-medium mt-1 flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">badge</span>
                {user.role}
              </p>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-4 py-8">
            <h3 className="text-lg font-bold text-text-main dark:text-text-main-dark">未登录</h3>
            <button onClick={() => navigate('/login')} className="bg-primary px-8 py-3 rounded-xl font-bold text-[#0f2906]">登录 / 注册</button>
          </div>
        )}
      </div>



      {/* Menu List */}
      <div className="flex flex-col px-4 pt-4 pb-24 gap-3">
        {user && user.role === 'coordinator' && (
          <button onClick={() => navigate('/add-pet')} className="flex items-center w-full p-4 bg-primary/20 rounded-2xl shadow-sm active:scale-[0.98] transition-transform">
            <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-[#0f2906] mr-4">
              <span className="material-symbols-outlined">add</span>
            </div>
            <div className="flex-1 text-left">
              <p className="text-text-main dark:text-white font-bold text-base">发布送养信息</p>
            </div>
            <span className="material-symbols-outlined text-gray-400">chevron_right</span>
          </button>
        )}

        {user && [
          ...(user.role !== 'coordinator' ? [{ icon: 'history', text: `领养记录 (${applications.length})`, path: '/adoption-history' }] : []),
          ...(user.role === 'coordinator' ? [
            { icon: 'assignment_ind', text: '收到的申请', path: '/coordinator/dashboard', hasNotification: receivedApplications.some(app => app.status !== 'approved' && app.status !== 'rejected') },
            { icon: 'pets', text: '我的发布', path: '/my-publications' }
          ] : []),
          { icon: 'help', text: '帮助中心', path: '/help' },
        ].map((item, index) => (
          <button
            key={index}
            onClick={() => item.path !== '#' && navigate(item.path)}
            className="flex items-center w-full p-4 bg-card-light dark:bg-card-dark rounded-2xl shadow-sm active:scale-[0.98] transition-transform"
          >
            <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary mr-4 relative">
              <span className="material-symbols-outlined">{item.icon}</span>
              {item.hasNotification && (
                <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border border-white dark:border-card-dark"></span>
                </span>
              )}
            </div>
            <div className="flex-1 text-left">
              <p className="text-text-main dark:text-white font-bold text-base">{item.text}</p>
            </div>
            <span className="material-symbols-outlined text-gray-400">chevron_right</span>
          </button>
        ))}

        {user && (
          <button onClick={logout} className="flex items-center w-full p-4 bg-red-50 dark:bg-red-900/10 rounded-2xl shadow-sm active:scale-[0.98] transition-transform mt-4">
            <div className="size-10 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center text-red-500 mr-4">
              <span className="material-symbols-outlined">logout</span>
            </div>
            <div className="flex-1 text-left">
              <p className="text-red-500 font-bold text-base">退出登录</p>
            </div>
          </button>
        )}
      </div>

      <BottomNav />
    </div>
  );
};

export default Profile;