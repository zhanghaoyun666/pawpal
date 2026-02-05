// AI 功能 API 服务
import { api } from './api';

// API 配置 - 确保正确的路径拼接
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
// 移除末尾的 /api 如果存在，避免重复
const CLEAN_BASE_URL = BASE_URL.replace(/\/api$/, '');
const AI_API_URL = `${CLEAN_BASE_URL}/api/ai/v2`;

console.log('[AI API] Base URL:', BASE_URL);
console.log('[AI API] AI API URL:', AI_API_URL);

// 智能问卷消息
export interface QuestionnaireMessage {
  role: 'user' | 'assistant';
  text: string;
}

// 智能问卷响应
export interface QuestionnaireResponse {
  next_question: string;
  is_complete: boolean;
  current_field: string;
  suggested_options: string[];
  explanation: string;
}

// 用户画像
export interface UserProfile {
  living_space?: string;
  experience_level?: string;
  daily_time_available?: number;
  family_status?: string;
  other_pets?: string[];
  activity_level?: string;
  preferences?: Record<string, any>;
}

// 匹配结果
export interface MatchResult {
  pet_id: string;
  pet_name: string;
  pet_image: string;
  score: number;
  reasons: string[];
  concerns: string[];
  compatibility: Record<string, number>;
}

// 预审结果
export interface PreCheckResult {
  passed: boolean;
  score: number;
  risk_level: 'low' | 'medium' | 'high';
  risk_points: Array<{ field: string; reason: string }>;
  suggestions: string[];
  auto_approved: boolean;
  review_report: string;
}

// AI API 服务
export const aiApi = {
  // ==================== 智能问卷 ====================
  
  // 获取下一个问卷问题
  getNextQuestion: async (
    userId: string,
    chatHistory: QuestionnaireMessage[],
    currentProfile: UserProfile = {},
    isFirst: boolean = false
  ): Promise<QuestionnaireResponse> => {
    const res = await fetch(`${AI_API_URL}/questionnaire/next`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        chat_history: chatHistory,
        current_profile: currentProfile,
        is_first: isFirst
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '获取问卷问题失败');
    }
    
    return res.json();
  },

  // 从对话提取用户画像
  extractProfile: async (chatHistory: QuestionnaireMessage[]): Promise<UserProfile> => {
    const res = await fetch(`${AI_API_URL}/questionnaire/extract-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_history: chatHistory })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '提取画像失败');
    }
    
    return res.json();
  },

  // ==================== 智能匹配 ====================
  
  // 获取推荐宠物
  getRecommendations: async (
    userId: string,
    userProfile: UserProfile,
    limit: number = 3
  ): Promise<MatchResult[]> => {
    const res = await fetch(`${AI_API_URL}/match/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        user_profile: userProfile,
        limit
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '获取推荐失败');
    }
    
    return res.json();
  },

  // 计算单个宠物匹配度
  calculateMatch: async (
    userProfile: UserProfile,
    petId: string
  ): Promise<MatchResult> => {
    const res = await fetch(`${AI_API_URL}/match/single`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_profile: userProfile,
        pet_id: petId
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '计算匹配度失败');
    }
    
    return res.json();
  },

  // ==================== AI 预审 ====================
  
  // 执行预审
  precheckApplication: async (
    applicationId: string,
    applicationData: Record<string, any>,
    userProfile: UserProfile,
    petId: string
  ): Promise<PreCheckResult> => {
    const res = await fetch(`${AI_API_URL}/precheck`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        application_id: applicationId,
        application_data: applicationData,
        user_profile: userProfile,
        pet_id: petId
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '预审失败');
    }
    
    return res.json();
  },

  // 获取预审状态
  getPrecheckStatus: async (applicationId: string): Promise<any> => {
    const res = await fetch(`${AI_API_URL}/precheck/status/${applicationId}`);
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '获取预审状态失败');
    }
    
    return res.json();
  },

  // ==================== 健康检查 ====================
  
  healthCheck: async (): Promise<{ status: string; model: string; api_configured: boolean }> => {
    const res = await fetch(`${AI_API_URL}/health`);
    
    if (!res.ok) {
      throw new Error('AI 服务健康检查失败');
    }
    
    return res.json();
  }
};

export default aiApi;
