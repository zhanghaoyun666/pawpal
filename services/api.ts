import { Pet, ChatSession, Message } from '../types';

// 使用环境变量配置API地址，支持开发和生产环境
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// 获取认证令牌
const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export const api = {
    getPets: async (ownerId?: string): Promise<Pet[]> => {
        const url = ownerId ? `${API_BASE_URL}/pets?owner_id=${ownerId}` : `${API_BASE_URL}/pets`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch pets');
        return res.json();
    },

    getPet: async (id: string): Promise<Pet> => {
        const res = await fetch(`${API_BASE_URL}/pets/${id}`);
        if (!res.ok) throw new Error('Failed to fetch pet');
        return res.json();
    },

    getFavorites: async (): Promise<string[]> => {
        const res = await fetch(`${API_BASE_URL}/users/favorites`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Failed to fetch favorites');
        return res.json();
    },

    toggleFavorite: async (petId: string) => {
        const res = await fetch(`${API_BASE_URL}/users/favorites/${petId}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            }
        });
        if (!res.ok) throw new Error('Failed to toggle favorite');
        return res.json();
    },

    getChats: async (userId: string): Promise<ChatSession[]> => {
        const res = await fetch(`${API_BASE_URL}/chats?user_id=${userId}`);
        if (!res.ok) throw new Error('Failed to fetch chats');
        return res.json();
    },

    getMessages: async (chatId: string, userId: string): Promise<Message[]> => {
        const res = await fetch(`${API_BASE_URL}/chats/${chatId}/messages?user_id=${userId}`);
        if (!res.ok) throw new Error('Failed to fetch messages');
        return res.json();
    },

    sendMessage: async (chatId: string, text: string, userId: string) => {
        const res = await fetch(`${API_BASE_URL}/chats/${chatId}/messages?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: chatId, text, sender_id: userId })
        });
        if (!res.ok) throw new Error('Failed to send message');
        return res.json();
    },

    markAsRead: async (chatId: string, userId: string) => {
        const res = await fetch(`${API_BASE_URL}/chats/${chatId}/read?user_id=${userId}`, {
            method: 'PUT'
        });
        if (!res.ok) throw new Error('Failed to mark as read');
        return res.json();
    },

    deleteMessage: async (chatId: string, messageId: string, userId: string) => {
        const res = await fetch(`${API_BASE_URL}/chats/${chatId}/messages/${messageId}?user_id=${userId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete message');
        return res.json();
    },

    deleteChat: async (chatId: string, userId: string) => {
        const res = await fetch(`${API_BASE_URL}/chats/${chatId}?user_id=${userId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete chat');
        return res.json();
    },

    deleteApplication: async (id: string, userId: string) => {
        const res = await fetch(`${API_BASE_URL}/applications/${id}?user_id=${userId}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to delete application');
        }
        return res.json();
    },

    submitApplication: async (data: any) => {
        const res = await fetch(`${API_BASE_URL}/applications`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to submit application');
        return res.json();
    },

    getApplications: async (userId: string) => {
        const res = await fetch(`${API_BASE_URL}/applications?user_id=${userId}`);
        if (!res.ok) throw new Error('Failed to fetch applications');
        return res.json();
    },

    getReceivedApplications: async (userId: string) => {
        const res = await fetch(`${API_BASE_URL}/applications/received?user_id=${userId}`);
        if (!res.ok) throw new Error('Failed to fetch received applications');
        return res.json();
    },

    updateApplicationStatus: async (id: string, status: string) => {
        const res = await fetch(`${API_BASE_URL}/applications/${id}/status?status=${status}`, {
            method: 'PUT'
        });
        if (!res.ok) throw new Error('Failed to update application status');
        return res.json();
    },

    register: async (data: any) => {
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Registration failed');
        }
        return res.json();
    },

    login: async (data: any) => {
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        return res.json();
    },

    createPet: async (data: any) => {
        const res = await fetch(`${API_BASE_URL}/pets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to create pet');
        }
        return res.json();
    },

    deletePet: async (id: string) => {
        const res = await fetch(`${API_BASE_URL}/pets/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to delete pet');
        }
        return res.json();
    }
};