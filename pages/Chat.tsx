import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Message, MessageStatus } from '../types';
import { useChatSSE } from '../hooks/useChatSSE';

// 消息发送状态
interface MessageWithStatus extends Message {
  status?: MessageStatus;
  tempId?: string;
}

// 格式化时间显示
const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString([], { month: '2-digit', day: '2-digit' });
};

// 格式化消息时间（聊天内）
const formatMessageTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const Chat: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();
  const { chats, user, refreshChats, markChatAsReadLocally } = useApp();
  
  // 从URL参数获取用户ID和宠物ID
  const urlParams = new URLSearchParams(location.search);
  const urlUserId = urlParams.get('user_id');
  const urlPetId = urlParams.get('pet_id');
  
  const [chatForApplicant, setChatForApplicant] = useState<string | null>(null);
  const effectiveChatId = chatForApplicant || id;

  const [messages, setMessages] = useState<MessageWithStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const chatInfo = chats.find(c => c.id === effectiveChatId);

  // 处理新消息（SSE 接收）
  const handleNewMessage = useCallback((msg: Message) => {
    setMessages(prev => {
      // 检查是否已存在（避免重复）
      if (prev.some(m => m.id === msg.id)) {
        return prev;
      }
      return [...prev, { ...msg, status: 'sent' as MessageStatus }];
    });
    
    // 发送已读回执
    if (effectiveChatId && user) {
      api.markAsRead(effectiveChatId, user.id).catch(console.error);
    }
    
    // 刷新聊天列表
    refreshChats().catch(console.error);
  }, [effectiveChatId, user, refreshChats]);

  // 处理消息已读（SSE 接收）
  const handleMessagesRead = useCallback((userId: string, count: number) => {
    console.log(`用户 ${userId} 已读 ${count} 条消息`);
    // 更新本地消息的已读状态
    setMessages(prev => prev.map(msg => ({
      ...msg,
      isRead: true
    })));
  }, []);

  // SSE Hook
  const {
    status: sseStatus,
    isConnected,
    subscribe,
    unsubscribe,
    connect: connectSSE,
    disconnect: disconnectSSE
  } = useChatSSE({
    userId: user?.id,
    chatId: effectiveChatId,
    onNewMessage: handleNewMessage,
    onMessagesRead: handleMessagesRead
  });

  // 加载历史消息
  const loadMessages = useCallback(async (chatId: string, showLoading = false) => {
    if (!user) return;
    if (showLoading) setLoading(true);
    
    try {
      const fetchedMessages = await api.getMessages(chatId, user.id);
      setMessages(fetchedMessages.map((m: Message) => ({ ...m, status: 'sent' as MessageStatus })));
    } catch (err) {
      console.error("加载消息失败:", err);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [user]);

  // 初始加载
  useEffect(() => {
    if (!effectiveChatId || !user) return;

    setLoading(true);
    setMessages([]);
    markChatAsReadLocally(effectiveChatId);

    // 加载历史消息
    loadMessages(effectiveChatId, true).then(() => {
      // 连接 SSE
      connectSSE();
    });

    // 清理函数
    return () => {
      if (effectiveChatId) {
        unsubscribe(effectiveChatId);
      }
      disconnectSSE();
    };
  }, [effectiveChatId, user, connectSSE, disconnectSSE, unsubscribe, loadMessages, markChatAsReadLocally]);

  // SSE 连接成功后订阅聊天室
  useEffect(() => {
    if (isConnected && effectiveChatId) {
      subscribe(effectiveChatId);
      // 发送已读回执
      if (user) {
        api.markAsRead(effectiveChatId, user.id).catch(console.error);
      }
    }
  }, [isConnected, effectiveChatId, subscribe, user]);

  // 处理URL参数
  useEffect(() => {
    if (!urlUserId || !urlPetId || !user) return;

    const findOrCreateChat = async () => {
      try {
        const allUserChats = await api.getChats(user.id);
        
        const targetChat = allUserChats.find(chat => 
          chat.petId === urlPetId && 
          chat.otherParticipantRole === 'user'
        );
        
        if (targetChat) {
          setChatForApplicant(targetChat.id);
        } else {
          alert('未找到与该申请人的对话，请联系管理员');
          navigate('/chat');
        }
      } catch (error) {
        console.error('查找对话失败:', error);
        navigate('/chat');
      }
    };
    
    findOrCreateChat();
  }, [urlUserId, urlPetId, user, navigate]);

  // 自动滚动到底部
  useEffect(() => {
    if (!loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  // 发送消息
  const handleSend = async () => {
    if (!inputText.trim() || !effectiveChatId || !user) return;

    const text = inputText.trim();
    const tempId = `temp-${Date.now()}`;
    const optimisticMessage: MessageWithStatus = {
      id: tempId,
      tempId,
      sender: 'user',
      text: text,
      timestamp: new Date().toISOString(),
      isRead: false,
      status: 'sending'
    };

    // 乐观更新
    setMessages(prev => [...prev, optimisticMessage]);
    setInputText('');
    
    // 重置textarea高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      await api.sendMessage(effectiveChatId, text, user.id);
      
      setMessages(prev => 
        prev.map(msg => 
          msg.tempId === tempId 
            ? { ...msg, status: 'sent' }
            : msg
        )
      );
      
      // 刷新消息列表
      setTimeout(() => {
        loadMessages(effectiveChatId);
        refreshChats().catch(console.error);
      }, 500);
    } catch (error) {
      console.error("发送消息失败:", error);
      setMessages(prev => 
        prev.map(msg => 
          msg.tempId === tempId 
            ? { ...msg, status: 'failed' }
            : msg
        )
      );
    }
  };

  // 重发失败的消息
  const handleRetry = async (failedMsg: MessageWithStatus) => {
    if (!effectiveChatId || !user) return;

    setMessages(prev => 
      prev.map(msg => 
        msg.tempId === failedMsg.tempId 
          ? { ...msg, status: 'sending' }
          : msg
      )
    );

    try {
      await api.sendMessage(effectiveChatId, failedMsg.text, user.id);
      setMessages(prev => 
        prev.map(msg => 
          msg.tempId === failedMsg.tempId 
            ? { ...msg, status: 'sent' }
            : msg
        )
      );
      setTimeout(() => loadMessages(effectiveChatId), 500);
    } catch (error) {
      setMessages(prev => 
        prev.map(msg => 
          msg.tempId === failedMsg.tempId 
            ? { ...msg, status: 'failed' }
            : msg
        )
      );
    }
  };

  // 处理输入
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    
    // 自动调整高度
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
  };

  // 发送图片
  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !effectiveChatId || !user) return;

    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('图片大小不能超过5MB');
      return;
    }

    setIsUploading(true);
    const tempId = `temp-img-${Date.now()}`;
    
    try {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const imageUrl = event.target?.result as string;
        
        const optimisticMessage: MessageWithStatus = {
          id: tempId,
          tempId,
          sender: 'user',
          text: `[图片]`,
          timestamp: new Date().toISOString(),
          isRead: false,
          status: 'sending',
          imageUrl
        };
        
        setMessages(prev => [...prev, optimisticMessage]);
        
        try {
          await api.sendMessage(effectiveChatId, `[图片] ${imageUrl}`, user.id);
          
          setMessages(prev => 
            prev.map(msg => 
              msg.tempId === tempId 
                ? { ...msg, status: 'sent' }
                : msg
            )
          );
          
          setTimeout(() => {
            loadMessages(effectiveChatId);
            refreshChats().catch(console.error);
          }, 500);
        } catch (error) {
          setMessages(prev => 
            prev.map(msg => 
              msg.tempId === tempId 
                ? { ...msg, status: 'failed' }
                : msg
            )
          );
        } finally {
          setIsUploading(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error("上传图片失败:", error);
      setIsUploading(false);
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 删除消息
  const handleDeleteMessage = async (messageId: string) => {
    if (!effectiveChatId || !user || !window.confirm('确定要删除这条消息吗？')) return;
    
    setMessages(prev => prev.filter(m => m.id !== messageId && m.tempId !== messageId));
    
    try {
      await api.deleteMessage(effectiveChatId, messageId, user.id);
    } catch (error) {
      console.error("删除消息失败:", error);
      loadMessages(effectiveChatId);
    }
  };

  // 渲染消息状态图标
  const renderMessageStatus = (status?: MessageStatus) => {
    switch (status) {
      case 'sending':
        return <span className="material-symbols-outlined text-[12px] text-gray-400 animate-spin">progress_activity</span>;
      case 'failed':
        return <span className="material-symbols-outlined text-[12px] text-red-500" title="发送失败">error</span>;
      case 'sent':
      default:
        return null;
    }
  };

  // 渲染连接状态
  const renderConnectionStatus = () => {
    if (sseStatus === 'connecting') {
      return (
        <span className="text-[10px] text-gray-400 flex items-center gap-1">
          <span className="material-symbols-outlined text-[12px] animate-spin">progress_activity</span>
          连接中...
        </span>
      );
    }
    if (sseStatus === 'error') {
      return (
        <span className="text-[10px] text-red-400 flex items-center gap-1">
          <span className="material-symbols-outlined text-[12px]">error</span>
          连接失败
        </span>
      );
    }
    if (isConnected) {
      return (
        <span className="text-[10px] text-green-500 flex items-center gap-1">
          <span className="material-symbols-outlined text-[12px]">check_circle</span>
          实时
        </span>
      );
    }
    return null;
  };

  if (!chatInfo) return (
    <div className="flex flex-col items-center justify-center h-screen bg-background-light dark:bg-background-dark p-4 text-center">
      <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
        <span className="material-symbols-outlined text-4xl text-gray-400">chat_error</span>
      </div>
      <h2 className="text-xl font-bold text-text-main dark:text-white mb-2">未找到对话</h2>
      <p className="text-gray-500 mb-6">该会话可能已被删除或 ID 无效。</p>
      <button
        onClick={() => navigate('/chat')}
        className="px-6 py-2 bg-primary text-[#0f2906] rounded-xl font-bold shadow-md hover:opacity-90 transition-opacity"
      >
        返回列表
      </button>
    </div>
  );

  return (
    <div className="bg-background-light dark:bg-background-dark font-display h-screen flex flex-col overflow-hidden max-w-md mx-auto shadow-2xl">
      {/* Header */}
      <header className="shrink-0 bg-background-light dark:bg-background-dark border-b border-gray-200 dark:border-gray-800 z-10">
        <div className="flex items-center p-4 pb-2 justify-between">
          <button onClick={() => navigate(-1)} className="text-text-main dark:text-text-main-dark flex size-12 shrink-0 items-center justify-start hover:opacity-70 transition-opacity">
            <span className="material-symbols-outlined text-2xl">arrow_back</span>
          </button>
          <div className="flex-1 text-center">
            <h2 className="text-text-main dark:text-text-main-dark text-lg font-bold leading-tight tracking-tight truncate px-2">
              {chatInfo.otherParticipantName}
            </h2>
            <div className="flex items-center justify-center gap-2">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {chatInfo.otherParticipantRole === 'coordinator' ? '协调员' : '申请人'}
              </p>
              {renderConnectionStatus()}
            </div>
          </div>
          <div className="flex w-12 items-center justify-end">
            <button
              onClick={() => navigate(`/details/${chatInfo.petId}`, { state: { from: location.pathname } })}
              className="flex items-center justify-center rounded-xl h-12 text-text-main dark:text-text-main-dark hover:opacity-70 transition-opacity"
            >
              <span className="material-symbols-outlined text-2xl">info</span>
            </button>
          </div>
        </div>
      </header>

      {/* Pet Context Bar */}
      <div className="shrink-0 bg-card-light dark:bg-surface-dark border-b border-gray-100 dark:border-gray-800 shadow-sm z-10">
        <div className="flex items-center gap-4 px-4 py-3 justify-between">
          <div className="flex items-center gap-4">
            <div
              className="bg-center bg-no-repeat bg-cover rounded-full h-12 w-12 border-2 border-primary"
              style={{ backgroundImage: `url("${chatInfo.petImage}")` }}
            ></div>
            <div className="flex flex-col justify-center">
              <p className="text-text-main dark:text-text-main-dark text-base font-bold leading-tight">{chatInfo.petName}</p>
              <p className="text-text-muted dark:text-text-muted text-xs font-medium mt-0.5">正在咨询中</p>
            </div>
          </div>
          <button
            onClick={() => navigate(`/details/${chatInfo.petId}`, { state: { from: location.pathname } })}
            className="shrink-0 text-text-main dark:text-text-main-dark hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6 bg-background-light dark:bg-background-dark scroll-smooth">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-gray-500 font-medium">加载聊天记录...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center px-8">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4 text-gray-400">
              <span className="material-symbols-outlined text-3xl">chat_bubble</span>
            </div>
            <p className="text-gray-500 font-medium">暂无消息</p>
            <p className="text-xs text-gray-400 mt-1">给对方发个招呼吧！</p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => {
              const isMe = msg.sender === 'user';
              const showAvatar = !isMe && (index === 0 || messages[index - 1].sender === 'user');
              const showTime = index === 0 || 
                new Date(msg.timestamp).getTime() - new Date(messages[index - 1].timestamp).getTime() > 5 * 60 * 1000;

              return (
                <React.Fragment key={msg.id || msg.tempId}>
                  {/* 时间分隔线 */}
                  {showTime && (
                    <div className="flex justify-center my-4">
                      <span className="text-[11px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full">
                        {formatTime(msg.timestamp)}
                      </span>
                    </div>
                  )}
                  
                  <div className={`flex items-end gap-3 ${isMe ? 'justify-end' : ''}`}>
                    {!isMe && (
                      <div
                        className={`bg-center bg-no-repeat bg-cover rounded-full w-8 h-8 shrink-0 border border-gray-200 dark:border-gray-700 ${showAvatar ? '' : 'opacity-0'}`}
                        style={{ backgroundImage: `url("${chatInfo.otherParticipantImage}")` }}
                      ></div>
                    )}

                    <div className={`group relative flex flex-col gap-1 ${isMe ? 'items-end' : 'items-start'} max-w-[85%]`}>
                      {!isMe && showAvatar && (
                        <p className="text-text-muted dark:text-text-muted text-[11px] font-medium ml-1">
                          {chatInfo.otherParticipantName} {chatInfo.otherParticipantRole === 'coordinator' ? '(协调员)' : ''}
                        </p>
                      )}
                      
                      {/* 图片消息 */}
                      {(msg as any).imageUrl ? (
                        <div className={`rounded-2xl overflow-hidden shadow-sm ${isMe ? 'rounded-br-none' : 'rounded-bl-none'}`}>
                          <img 
                            src={(msg as any).imageUrl} 
                            alt="图片" 
                            className="max-w-[200px] max-h-[200px] object-cover cursor-pointer"
                            onClick={() => window.open((msg as any).imageUrl, '_blank')}
                          />
                        </div>
                      ) : (
                        <div className={`text-sm sm:text-base font-normal leading-relaxed rounded-2xl px-4 py-3 shadow-sm ${isMe
                          ? 'rounded-br-none bg-primary text-[#0f2906]'
                          : 'rounded-bl-none bg-bubble-rec-light dark:bg-bubble-rec-dark text-text-main dark:text-text-main-dark'
                          }`}>
                          {msg.text.startsWith('[图片]') ? (
                            <img 
                              src={msg.text.replace('[图片] ', '')} 
                              alt="图片" 
                              className="max-w-[200px] max-h-[200px] object-cover rounded-lg cursor-pointer"
                              onClick={() => window.open(msg.text.replace('[图片] ', ''), '_blank')}
                            />
                          ) : (
                            msg.text
                          )}
                        </div>
                      )}
                      
                      {/* 消息底部：时间 + 状态 */}
                      <div className={`flex items-center gap-1 ${isMe ? 'mr-1' : 'ml-1'}`}>
                        <p className="text-text-muted dark:text-text-muted text-[10px] font-medium">
                          {formatMessageTime(msg.timestamp)}
                        </p>
                        {isMe && renderMessageStatus(msg.status)}
                      </div>
                      
                      {/* 失败重试按钮 */}
                      {isMe && msg.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(msg)}
                          className="absolute -left-16 top-1/2 -translate-y-1/2 px-2 py-1 bg-red-500 text-white text-xs rounded-full shadow-md hover:bg-red-600 transition-colors"
                        >
                          重试
                        </button>
                      )}
                      
                      {/* 删除按钮 */}
                      {isMe && msg.status !== 'sending' && (
                        <button
                          onClick={() => handleDeleteMessage(msg.id || msg.tempId!)}
                          className="absolute -left-8 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                          title="删除消息"
                        >
                          <span className="material-symbols-outlined text-lg">delete</span>
                        </button>
                      )}
                    </div>
                  </div>
                </React.Fragment>
              );
            })}
          </>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="shrink-0 bg-card-light dark:bg-surface-dark border-t border-gray-100 dark:border-gray-800 p-3 pb-6 sm:pb-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          {/* 图片上传 */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            className="hidden"
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            aria-label="发送图片"
            className="p-2 text-text-muted dark:text-text-muted hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors shrink-0 disabled:opacity-50"
          >
            <span className={`material-symbols-outlined text-2xl ${isUploading ? 'animate-pulse' : ''}`}>
              {isUploading ? 'hourglass_top' : 'image'}
            </span>
          </button>
          
          <div className="flex-1 bg-background-light dark:bg-background-dark rounded-xl flex items-center min-h-[48px] border border-transparent focus-within:border-primary/50 transition-colors">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="w-full bg-transparent border-0 focus:ring-0 text-text-main dark:text-text-main-dark placeholder-gray-400 dark:placeholder-gray-500 py-3 px-4 resize-none h-12 max-h-32 focus:outline-none"
              placeholder="请输入消息..."
              rows={1}
            ></textarea>
          </div>
          
          <button
            onClick={handleSend}
            disabled={!inputText.trim()}
            aria-label="Send message"
            className="p-3 bg-primary hover:bg-green-400 text-[#0f2906] rounded-full shadow-md transition-colors shrink-0 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-xl font-bold">send</span>
          </button>
        </div>
      </footer>
    </div>
  );
};

export default Chat;
