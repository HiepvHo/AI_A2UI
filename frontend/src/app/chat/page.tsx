'use client';

import { useState, useEffect, useRef } from 'react';
import type { ChatResponse, Message } from '@/types/chatbot';
import { sendChatMessage, getSessionId } from '@/lib/api';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import LoadingMessage from '@/components/LoadingMessage';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

const USER_ID = 1; // Hardcoded for testing

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Get session ID - only on client side
  const [sessionId, setSessionId] = useState<string>('');
  
  useEffect(() => {
    // Only get session ID on client side
    setSessionId(getSessionId());
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (query: string) => {
    if (!query.trim() || isLoading) return;

    const queryText = query.trim();
    const messageId = `msg_${Date.now()}`;
    
    // Thêm user message ngay lập tức (với response = null)
    const userMessage: Message = {
      id: messageId,
      query: queryText,
      response: null as any, // Sẽ được update sau
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        query: queryText,
        session_id: sessionId,
        user_id: USER_ID,
      });

      // Update message với response
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === messageId 
            ? { ...msg, response }
            : msg
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Lỗi không xác định';
      setError(errorMessage);
      console.error('Chat error:', err);
      
      // Xóa user message nếu có lỗi (hoặc giữ lại với error state)
      // Hoặc có thể thêm error message vào response
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-xl font-bold text-foreground">Emotion Chatbot</h1>
          <p className="text-sm text-muted-foreground">Hỗ trợ sức khỏe cảm xúc với AI</p>
        </div>
      </header>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-6xl mx-auto">
          {/* Welcome Message */}
          {messages.length === 0 && !isLoading && (
            <div className="mb-4">
              <Card className="max-w-[85%]">
                <CardContent className="p-4">
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Xin chào!
                  </h3>
                  <p className="text-foreground mb-3">
                    Tôi là chatbot hỗ trợ sức khỏe cảm xúc. Tôi có thể:
                  </p>
                  <ul className="list-disc list-inside text-foreground mb-3 space-y-1">
                    <li>Lắng nghe và tư vấn về cảm xúc</li>
                    <li>Phân tích thống kê tâm trạng</li>
                    <li>Gợi ý cách giảm stress, lo âu</li>
                    <li>Phát hiện dấu hiệu khủng hoảng</li>
                  </ul>
                  <p className="text-sm text-muted-foreground">
                    Hãy bắt đầu bằng cách chia sẻ cảm xúc của bạn hoặc đặt câu hỏi.
                  </p>
                </CardContent>
              </Card>
      </div>
          )}

      {/* Messages */}
          {messages.map((message) => (
            <div key={message.id}>
              {/* User message - hiển thị ngay khi nhấn gửi */}
              <ChatMessage
                query={message.query}
                response={message.response || {} as ChatResponse}
                isUser={true}
              />
              {/* Bot response - chỉ hiển thị khi có response */}
              {message.response && (
                <ChatMessage
                  query={message.query}
                  response={message.response}
                  isUser={false}
                />
              )}
            </div>
          ))}

          {/* Loading */}
          {isLoading && <LoadingMessage />}

          {/* Error */}
          {error && (
            <div className="mb-4">
              <Alert variant="destructive" className="max-w-[85%]">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Lỗi kết nối</AlertTitle>
                <AlertDescription>
                  {error}
                  <div className="mt-2 text-xs">
                    Kiểm tra: Server đang chạy? (http://localhost:8000)
                  </div>
                </AlertDescription>
              </Alert>
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

