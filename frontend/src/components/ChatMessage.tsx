'use client';

import type { ChatResponse } from '@/types/chatbot';
import A2UIRenderer from './a2ui/A2UIRenderer';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Clock } from 'lucide-react';

interface ChatMessageProps {
  query: string;
  response: ChatResponse;
  isUser: boolean;
}

export default function ChatMessage({ query, response, isUser }: ChatMessageProps) {
  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <Card className="max-w-full bg-primary text-primary-foreground border-0 rounded-none shadow-md">
          <CardContent className="p-3">
            <p className="text-sm text-[#E6ECF5]">{query}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Bot message - chỉ hiển thị khi có response
  if (!response) {
    return null;
  }

  return (
    <div className="flex justify-start mb-4">
      <Card className="max-w-full bg-slate-900/80 border-0 rounded-none text-foreground shadow-md">
        <CardContent className="p-4">
          {/* Crisis Alert */}
          {response.crisis_detected && (
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>CẢNH BÁO: Phát hiện dấu hiệu khủng hoảng!</AlertTitle>
              <AlertDescription>
                Vui lòng liên hệ đường dây nóng: <strong>1900 0099</strong> (24/7)
              </AlertDescription>
            </Alert>
          )}

          {/* A2UI Blocks */}
          {response.a2ui_blocks && response.a2ui_blocks.length > 0 ? (
            <A2UIRenderer blocks={response.a2ui_blocks} />
          ) : (
            <p className="whitespace-pre-wrap text-[#E6ECF5]">{response.answer}</p>
          )}

          {/* Processing Time */}
          {response.processing_time && (
            <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{response.processing_time.toFixed(2)}s</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

