'use client';

import type { ChatResponse } from '@/types/chatbot';
import A2UIRenderer from './a2ui/A2UIRenderer';

interface ChatMessageProps {
  query: string;
  response: ChatResponse;
  isUser: boolean;
}

export default function ChatMessage({ query, response, isUser }: ChatMessageProps) {
  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[70%] bg-blue-600 text-white px-4 py-3 rounded-2xl">
          <p className="text-sm">{query}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%] bg-white px-4 py-3 rounded-xl border border-gray-200 shadow-sm">
        {/* Crisis Alert */}
        {response.crisis_detected && (
          <div className="mb-3 p-3 bg-red-50 border-2 border-red-500 rounded-lg">
            <div className="font-semibold text-red-800 mb-1">
              CẢNH BÁO: Phát hiện dấu hiệu khủng hoảng!
            </div>
            <div className="text-sm text-red-700">
              Vui lòng liên hệ đường dây nóng: <strong>1900 0099</strong> (24/7)
            </div>
          </div>
        )}

        {/* A2UI Blocks */}
        {response.a2ui_blocks && response.a2ui_blocks.length > 0 ? (
          <A2UIRenderer blocks={response.a2ui_blocks} />
        ) : (
          <p className="text-gray-800 whitespace-pre-wrap">{response.answer}</p>
        )}

        {/* Sources */}
        {response.sources && response.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="text-xs font-semibold text-gray-700 mb-2">
              Nguồn tri thức:
            </div>
            <div className="space-y-1">
              {response.sources.map((source, index) => {
                const score = source.relevance_score || source.score || 0;
                const category = source.category || 'Chung';
                const title = source.title || source.source_file || 'Tài liệu';
                return (
                  <div key={index} className="text-xs text-gray-600">
                    {index + 1}. <span className="font-medium">{category}</span> - {title}
                    <span className="text-gray-500 ml-1">
                      ({(score * 100).toFixed(1)}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Processing Time */}
        {response.processing_time && (
          <div className="mt-2 text-xs text-gray-400">
            ⏱️ {response.processing_time.toFixed(2)}s
          </div>
        )}
      </div>
    </div>
  );
}

