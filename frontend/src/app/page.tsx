'use client';

import { useEffect, useRef, useState } from 'react';
import type { ChatResponse, Message } from '@/types/chatbot';
import { getSessionId, sendChatMessage } from '@/lib/api';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import LoadingMessage from '@/components/LoadingMessage';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Sparkles } from 'lucide-react';

const DEFAULT_USER_ID =
  Number(process.env.NEXT_PUBLIC_DEFAULT_USER_ID || 1) || 1;

export default function HomeChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [isChatting, setIsChatting] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (isChatting) {
      chatContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isChatting]);

  const handleSendMessage = async (query: string) => {
    if (!query.trim() || isLoading) return;

    const queryText = query.trim();
    const messageId = `msg_${Date.now()}`;
    if (!isChatting) setIsChatting(true);

    const userMessage: Message = {
      id: messageId,
      query: queryText,
      response: null,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        query: queryText,
        session_id: sessionId,
        user_id: DEFAULT_USER_ID,
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, response } : msg
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Lỗi không xác định';
      setError(errorMessage);
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="relative min-h-screen overflow-hidden text-foreground">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(120,119,198,0.18),transparent_25%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_25%),radial-gradient(circle_at_50%_80%,rgba(56,189,248,0.1),transparent_30%),radial-gradient(circle,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[length:900px_900px,700px_700px,900px_900px,24px_24px]" />
      <div
        className={`relative z-10 mx-auto flex flex-col px-4 sm:px-6 ${
          isChatting ? 'w-full max-w-none gap-4 py-4' : 'max-w-6xl gap-8 py-12'
        }`}
      >
        <header
          className={`space-y-4 text-center transition-all duration-300 ${
            isChatting ? 'opacity-0 -translate-y-4 h-0 overflow-hidden pointer-events-none' : 'opacity-100 translate-y-0'
          }`}
        >
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/15 px-4 py-2 text-sm text-primary">
            <Sparkles className="h-4 w-4" />
            <span>AI cảm xúc + biểu đồ tương tác</span>
          </div>
          <div className="space-y-3">
            <h1 className="text-4xl font-bold leading-tight sm:text-5xl md:text-6xl text-[#E6ECF5]">
              Chatbot cảm xúc <br />
              <span className="text-primary">ấm áp & trực quan</span>
            </h1>
          </div>
          <div className="flex flex-wrap justify-center gap-2 text-sm text-muted-foreground">
            {[
              'RAG',
              'Groq Llama 3.3 70B',
              'Plotly tương tác',
              'SQL filter realtime',
              'A2UI blocks',
            ].map((item) => (
              <Badge key={item} variant="secondary" className="bg-secondary/60 text-foreground">
                {item}
              </Badge>
            ))}
          </div>

          <div className="flex flex-wrap justify-center gap-2 text-xs text-muted-foreground">
            {['Vui', 'Buồn', 'Lo âu', 'Stress công việc', 'Quan hệ', 'Ngủ nghỉ', 'Tự tin'].map((item) => (
              <Badge key={item} variant="outline" className="border-slate-700 bg-slate-900/30 text-foreground">
                {item}
              </Badge>
            ))}
          </div>
        </header>

        <Card
          ref={chatContainerRef}
          className={`bg-slate-900/85 shadow-none backdrop-blur border-0 rounded-none ${
            isChatting ? 'w-full' : ''
          }`}
        >
          <CardContent className="p-0 flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800/60 px-6 py-4">
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-muted-foreground">
                  Emotion Chatbot
                </p>
                <h2 className="text-2xl font-semibold text-foreground">
                  Hỏi bất cứ điều gì, mình lắng nghe
                </h2>
              </div>
              <Badge className="border-primary/40 bg-primary/20 text-primary">
                TÔI LUÔN Ở ĐÂY
              </Badge>
            </div>

            <div
              className={`chat-scroll space-y-4 overflow-y-auto px-6 py-6 ${
                hasMessages || isChatting
                  ? 'flex-1 min-h-[calc(100vh-230px)] max-h-[calc(100vh-240px)]'
                  : 'max-h-[520px]'
              }`}
            >

              {messages.map((message) => (
                <div key={message.id}>
                  <ChatMessage
                    query={message.query}
                    response={(message.response || {}) as ChatResponse}
                    isUser={true}
                  />
                  {message.response && (
                    <ChatMessage
                      query={message.query}
                      response={message.response}
                      isUser={false}
                    />
                  )}
                </div>
              ))}

              {isLoading && <LoadingMessage />}

              {error && (
                <Alert variant="destructive" className="border-red-500/50 bg-red-500/10">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Lỗi kết nối</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div ref={messagesEndRef} />
            </div>

            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder="Nhập câu hỏi hoặc yêu cầu phân tích cảm xúc..."
              className="border-t border-slate-800/60 bg-secondary/20"
              inputClassName="bg-slate-900/70 border-slate-800 text-foreground placeholder:text-slate-500 focus-visible:ring-primary"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

