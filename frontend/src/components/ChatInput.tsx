'use client';

import { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  placeholder?: string;
}

export default function ChatInput({
  onSendMessage,
  disabled,
  className = '',
  inputClassName = '',
  placeholder = 'Nhập câu hỏi của bạn...',
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`border-t bg-background p-4 shadow-sm ${className}`}
    >
      <div className="flex gap-2 max-w-6xl mx-auto">
        <Input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          className={`flex-1 rounded-full ${inputClassName}`}
        />
        <Button
          type="submit"
          disabled={disabled || !input.trim()}
          size="icon"
          className="rounded-full h-10 w-10 shrink-0"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Gửi</span>
        </Button>
      </div>
    </form>
  );
}

