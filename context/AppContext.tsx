import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Pet, ChatSession } from '../types';
import { api } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar_url?: string;
}

interface AppContextType {
  pets: Pet[];
  favorites: string[];
  toggleFavorite: (id: string) => void;
  isFavorite: (id: string) => boolean;
  chats: ChatSession[];
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
  refreshData: () => Promise<void>;
  refreshPets: () => Promise<void>;
  refreshChats: () => Promise<void>;
  refreshApplications: () => Promise<void>;
  refreshReceivedApplications: () => Promise<void>;
  markChatAsReadLocally: (chatId: string) => void;
  applications: any[];
  receivedApplications: any[];
  refreshMyPets: () => Promise<Pet[]>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [applications, setApplications] = useState<any[]>([]);
  const [receivedApplications, setReceivedApplications] = useState<any[]>([]);

  const refreshPets = React.useCallback(async () => {
    try {
      // 首页不显示已领养的宠物
      const fetchedPets = await api.getPets();
      setPets(fetchedPets);
      
      // 只有在用户已登录时才获取收藏数据
      if (user) {
        try {
          const fetchedFavorites = await api.getFavorites();
          setFavorites(fetchedFavorites);
        } catch (error) {
          console.error("Failed to fetch favorites:", error);
          // 如果获取收藏失败，清空收藏列表
          setFavorites([]);
        }
      } else {
        // 未登录时清空收藏列表
        setFavorites([]);
      }
    } catch (error) {
      console.error("Failed to fetch pets:", error);
    }
  }, [user]);

  // 新增函数：获取用户发布的所有宠物（包括已领养的）
  const refreshMyPets = React.useCallback(async () => {
    if (!user) return;
    try {
      // 我的发布页面显示所有宠物，包括已领养的
      const myPets = await api.getPets(user.id, true);
      return myPets;
    } catch (error) {
      console.error("Failed to fetch my pets:", error);
      return [];
    }
  }, [user]);

  const refreshChats = React.useCallback(async () => {
    if (!user) return;
    try {
      const fetchedChats = await api.getChats(user.id);
      setChats(fetchedChats);
    } catch (error) {
      console.error("Failed to fetch chats:", error);
    }
  }, [user]);

  const refreshApplications = React.useCallback(async () => {
    if (!user) return;
    try {
      // 获取所有申请记录，包括已批准的
      const fetchedApps = await api.getApplications(user.id, true);
      setApplications(fetchedApps);
    } catch (error) {
      console.error("Failed to fetch apps:", error);
    }
  }, [user]);

  const refreshReceivedApplications = React.useCallback(async () => {
    if (!user || user.role !== 'coordinator') return;
    try {
      const fetchedApps = await api.getReceivedApplications(user.id);
      setReceivedApplications(fetchedApps);
    } catch (error) {
      console.error("Failed to fetch received applications:", error);
    }
  }, [user]);

  const refreshData = React.useCallback(async () => {
    setIsLoading(true);
    await Promise.all([
      refreshPets(),
      refreshChats(),
      refreshApplications(),
      refreshReceivedApplications()
    ]);
    setIsLoading(false);
  }, [refreshPets, refreshChats, refreshApplications, refreshReceivedApplications]);

  const markChatAsReadLocally = React.useCallback((chatId: string) => {
    setChats(prev => prev.map(chat =>
      chat.id === chatId ? { ...chat, unreadCount: 0 } : chat
    ));
  }, []);

  useEffect(() => {
    // 每次应用启动时都清除登录状态
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  useEffect(() => {
    refreshData();
  }, [user]);

  const login = (token: string, userData: User) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const toggleFavorite = async (id: string) => {
    // 只有在用户已登录时才允许收藏操作
    if (!user) {
      console.log("User must be logged in to toggle favorite");
      return;
    }
    
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(fid => fid !== id) : [...prev, id]
    );
    try {
      await api.toggleFavorite(id);
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  const isFavorite = (id: string) => favorites.includes(id);

  return (
    <AppContext.Provider value={{
      pets,
      favorites,
      toggleFavorite,
      isFavorite,
      chats,
      user,
      login,
      logout,
      isLoading,
      refreshData,
      refreshPets,
      refreshChats,
      refreshApplications,
      refreshReceivedApplications,
      markChatAsReadLocally,
      applications,
      receivedApplications,
      refreshMyPets
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};