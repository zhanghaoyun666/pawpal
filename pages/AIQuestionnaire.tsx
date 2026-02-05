import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiApi, QuestionnaireMessage, UserProfile } from '../services/aiApi';
import { useApp } from '../context/AppContext';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  options?: string[];
  field?: string;
  explanation?: string;
}

const AIQuestionnaire: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile>({});
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 自动滚动
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 初始化对话
  useEffect(() => {
    if (user && messages.length === 0 && !error) {
      startQuestionnaire();
    }
  }, [user]);

  const startQuestionnaire = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('[AI] 启动问卷...');
      const response = await aiApi.getNextQuestion(
        user?.id || 'guest',
        [],
        {},
        true
      );
      console.log('[AI] 收到响应:', response);

      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        text: '您好！我是 PawPal 智能领养顾问 🤖\n\n为了帮您找到最合适的毛孩子，我想先了解一些您的情况。这会是一次轻松的对话，大约需要 2-3 分钟。',
      };

      const firstQuestion: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        text: response.next_question,
        options: response.suggested_options,
        field: response.current_field,
        explanation: response.explanation,
      };

      setMessages([welcomeMessage, firstQuestion]);
    } catch (err: any) {
      console.error('[AI] 启动问卷失败:', err);
      setError(err.message || '服务启动失败');
      // 显示默认问题
      setMessages([{
        id: 'error',
        role: 'assistant',
        text: '抱歉，AI 服务暂时不可用。请刷新页面重试，或直接浏览宠物列表。'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (text: string = inputText) => {
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: text.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // 构建对话历史
      const chatHistory: QuestionnaireMessage[] = messages
        .filter(m => m.id !== 'welcome' && m.id !== 'error')
        .map(m => ({ role: m.role, text: m.text }));
      chatHistory.push({ role: 'user', text: text.trim() });

      // 更新当前画像
      const currentField = messages[messages.length - 1]?.field;
      const updatedProfile = { ...userProfile };
      if (currentField) {
        (updatedProfile as any)[currentField] = text.trim();
        setUserProfile(updatedProfile);
      }

      const response = await aiApi.getNextQuestion(
        user?.id || 'guest',
        chatHistory,
        updatedProfile,
        false
      );

      if (response.is_complete) {
        setIsComplete(true);
        // 提取完整画像
        const profile = await aiApi.extractProfile(chatHistory);
        setUserProfile(profile);

        const completeMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          text: response.next_question || '感谢您的时间！我已经了解了您的情况。\n\n现在让我为您推荐最适合的宠物...',
        };
        setMessages(prev => [...prev, completeMessage]);

        // 延迟后跳转到推荐页面
        setTimeout(() => {
          navigate('/ai-recommendations', { state: { profile } });
        }, 2000);
      } else {
        const nextMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          text: response.next_question,
          options: response.suggested_options,
          field: response.current_field,
          explanation: response.explanation,
        };
        setMessages(prev => [...prev, nextMessage]);
      }
    } catch (err: any) {
      console.error('[AI] 获取下一个问题失败:', err);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        text: '抱歉，遇到了一些问题。请重试或跳过此问题。'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptionClick = (option: string) => {
    handleSend(option);
  };

  const handleSkip = () => {
    handleSend('跳过');
  };

  const handleRetry = () => {
    setMessages([]);
    setError(null);
    startQuestionnaire();
  };

  // 未登录状态
  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background-light dark:bg-background-dark p-4">
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl text-gray-400 mb-4">lock</span>
          <h2 className="text-2xl font-bold mb-2 text-text-main dark:text-white">请先登录</h2>
          <p className="text-gray-500 mb-6">AI 智能匹配需要登录后才能使用</p>
          <button
            onClick={() => navigate('/login')}
            className="px-8 py-3 bg-primary text-[#0f2906] rounded-xl font-bold text-lg"
          >
            去登录
          </button>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error && messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background-light dark:bg-background-dark p-4">
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl text-red-400 mb-4">error</span>
          <h2 className="text-xl font-bold mb-2 text-text-main dark:text-white">服务暂时不可用</h2>
          <p className="text-gray-500 mb-2">{error}</p>
          <p className="text-gray-400 text-sm mb-6">请检查网络连接或稍后重试</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleRetry}
              className="px-6 py-2 bg-primary text-[#0f2906] rounded-xl font-bold"
            >
              重试
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 border-2 border-gray-300 text-gray-600 rounded-xl font-bold"
            >
              返回首页
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background-light dark:bg-background-dark h-screen flex flex-col max-w-md mx-auto">
      {/* Header */}
      <header className="bg-background-light dark:bg-background-dark border-b border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <div className="text-center">
            <h1 className="text-lg font-bold">智能领养顾问</h1>
            <p className="text-xs text-gray-500">AI 驱动的个性化推荐</p>
          </div>
          <div className="w-10" />
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-gray-500">正在启动 AI 顾问...</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-primary text-[#0f2906] rounded-br-none'
                      : 'bg-white dark:bg-card-dark border border-gray-100 dark:border-gray-800 rounded-bl-none'
                  }`}
                >
                  {msg.explanation && (
                    <div className="text-[10px] text-gray-400 mb-1 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">info</span>
                      {msg.explanation}
                    </div>
                  )}
                  
                  <p className="text-sm whitespace-pre-wrap">{msg.text}</p>

                  {msg.options && msg.options.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {msg.options.map((option, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleOptionClick(option)}
                          disabled={isLoading}
                          className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm transition-colors"
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-card-dark border border-gray-100 dark:border-gray-800 rounded-2xl rounded-bl-none px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      {!isComplete && messages.length > 0 && (
        <footer className="bg-white dark:bg-card-dark border-t border-gray-100 dark:border-gray-800 p-4">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="输入您的回答..."
              disabled={isLoading}
              className="flex-1 bg-gray-50 dark:bg-gray-800 border-0 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isLoading}
              className="p-3 bg-primary text-[#0f2906] rounded-xl disabled:opacity-50"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
          <button
            onClick={handleSkip}
            disabled={isLoading}
            className="mt-2 text-xs text-gray-400 hover:text-gray-600"
          >
            跳过此问题
          </button>
        </footer>
      )}
    </div>
  );
};

export default AIQuestionnaire;
