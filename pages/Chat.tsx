import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Message } from '../types';

const Chat: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();
  const { chats, user, refreshChats, markChatAsReadLocally } = useApp();

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Find chat info
  const chatInfo = chats.find(c => c.id === id);

  useEffect(() => {
    if (id && user) {
      // Only show loading spinner on initial entry or chat switch
      setLoading(true);
      setMessages([]); // Clear previous chat messages immediately

      // OPTIMISTIC: Immediately clear red dot in UI
      markChatAsReadLocally(id);

      // Parallelize fetches for better performance
      Promise.all([
        api.getMessages(id, user.id),
        api.markAsRead(id, user.id)
      ]).then(([fetchedMessages]) => {
        setMessages(fetchedMessages);
        setLoading(false);
        // Silently refresh chats to ensure server sync, but dot is already gone locally
        refreshChats().catch(console.error);
      }).catch(err => {
        console.error("Load failed", err);
        setLoading(false);
      });

      // Poll for messages every 5s for simple MVP real-time
      const interval = setInterval(() => {
        // Polling should NOT trigger loading state
        api.getMessages(id, user.id).then(setMessages).catch(console.error);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [id, user, refreshChats, markChatAsReadLocally]);

  useEffect(() => {
    if (!loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const handleSend = async () => {
    if (!inputText.trim() || !id || !user) return;

    const tempId = Date.now().toString();
    const optimisticMessage: Message = {
      id: tempId,
      sender: 'user',
      text: inputText,
      timestamp: new Date().toISOString(),
      isRead: false
    };

    setMessages(prev => [...prev, optimisticMessage]);
    setInputText('');

    try {
      await api.sendMessage(id, inputText, user.id);
      // Refresh to get server timestamp/ID
      const updatedMessages = await api.getMessages(id, user.id);
      setMessages(updatedMessages);
    } catch (error) {
      console.error("Failed to send", error);
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (!id || !user || !window.confirm('确定要删除这条消息吗？')) return;
    try {
      await api.deleteMessage(id, messageId, user.id);
      setMessages(prev => prev.filter(m => m.id !== messageId));
    } catch (error) {
      console.error("Failed to delete message", error);
    }
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
          <h2 className="text-text-main dark:text-text-main-dark text-lg font-bold leading-tight tracking-tight flex-1 text-center truncate px-2">
            {chatInfo.otherParticipantName}
          </h2>
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
          messages.map((msg, index) => {
            const isMe = msg.sender === 'user';
            const showAvatar = !isMe && (index === 0 || messages[index - 1].sender === 'user');

            return (
              <div key={msg.id} className={`flex items-end gap-3 ${isMe ? 'justify-end' : ''}`}>
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
                  <div className={`text-sm sm:text-base font-normal leading-relaxed rounded-2xl px-4 py-3 shadow-sm ${isMe
                    ? 'rounded-br-none bg-primary text-[#0f2906]'
                    : 'rounded-bl-none bg-bubble-rec-light dark:bg-bubble-rec-dark text-text-main dark:text-text-main-dark'
                    }`}>
                    {msg.text}
                  </div>
                  {isMe && (
                    <button
                      onClick={() => handleDeleteMessage(msg.id)}
                      className="absolute -left-8 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                      title="删除消息"
                    >
                      <span className="material-symbols-outlined text-lg">delete</span>
                    </button>
                  )}
                  <p className={`text-text-muted dark:text-text-muted text-[10px] font-medium ${isMe ? 'mr-1' : 'ml-1'}`}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="shrink-0 bg-card-light dark:bg-surface-dark border-t border-gray-100 dark:border-gray-800 p-3 pb-6 sm:pb-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <button aria-label="Add attachment" className="p-2 text-text-muted dark:text-text-muted hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors shrink-0">
            <span className="material-symbols-outlined text-2xl">add_circle</span>
          </button>
          <div className="flex-1 bg-background-light dark:bg-background-dark rounded-xl flex items-center min-h-[48px] border border-transparent focus-within:border-primary/50 transition-colors">
            <textarea
              value={inputText}
              onChange={(e) => {
                setInputText(e.target.value);
                // Auto resize textarea
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                  // Reset height
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                }
              }}
              className="w-full bg-transparent border-0 focus:ring-0 text-text-main dark:text-text-main-dark placeholder-gray-400 dark:placeholder-gray-500 py-3 px-4 resize-none h-12 max-h-32 focus:outline-none"
              placeholder="请输入消息..."
              rows={1}
            ></textarea>
            <button aria-label="Send photo" className="mr-2 p-2 text-text-muted dark:text-text-muted hover:text-primary transition-colors rounded-full">
              <span className="material-symbols-outlined text-[20px]">image</span>
            </button>
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