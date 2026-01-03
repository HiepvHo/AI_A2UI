'use client';

import { useState, useEffect, useRef } from 'react';
import type { ChatResponse, Message } from '@/types/chatbot';
import { sendChatMessage, getSessionId } from '@/lib/api';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import LoadingMessage from '@/components/LoadingMessage';

const USER_ID = 1; // Hardcoded for testing

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Get session ID once on mount
  const [sessionId] = useState(() => getSessionId());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (query: string) => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        query,
        session_id: sessionId,
        user_id: USER_ID,
      });

      const newMessage: Message = {
        id: `msg_${Date.now()}`,
        query,
        response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, newMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Lỗi không xác định';
      setError(errorMessage);
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-xl font-bold text-gray-800">Emotion Chatbot</h1>
          <p className="text-sm text-gray-600">Hỗ trợ sức khỏe cảm xúc với AI</p>
        </div>
      </header>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-6xl mx-auto">
          {/* Welcome Message */}
          {messages.length === 0 && !isLoading && (
            <div className="mb-4">
              <div className="max-w-[85%] bg-white px-4 py-3 rounded-xl border border-gray-200 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  Xin chào!
                </h3>
                <p className="text-gray-700 mb-3">
                  Tôi là chatbot hỗ trợ sức khỏe cảm xúc. Tôi có thể:
                </p>
                <ul className="list-disc list-inside text-gray-700 mb-3 space-y-1">
                  <li>Lắng nghe và tư vấn về cảm xúc</li>
                  <li>Phân tích thống kê tâm trạng</li>
                  <li>Gợi ý cách giảm stress, lo âu</li>
                  <li>Phát hiện dấu hiệu khủng hoảng</li>
                </ul>
                <p className="text-sm text-gray-600">
                  Hãy bắt đầu bằng cách chia sẻ cảm xúc của bạn hoặc đặt câu hỏi.
                </p>
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <div key={message.id}>
              <ChatMessage
                query={message.query}
                response={message.response}
                isUser={true}
              />
              <ChatMessage
                query={message.query}
                response={message.response}
                isUser={false}
              />
            </div>
          ))}

          {/* Loading */}
          {isLoading && <LoadingMessage />}

          {/* Error */}
          {error && (
            <div className="mb-4">
              <div className="max-w-[85%] bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                <div className="font-semibold text-red-800 mb-1">Lỗi kết nối</div>
                <div className="text-sm text-red-700">{error}</div>
                <div className="text-xs text-red-600 mt-2">
                  Kiểm tra: Server đang chạy? (http://localhost:8000)
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  );
}

