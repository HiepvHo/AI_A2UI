'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import type { A2UIChartBlock } from '@/types/chatbot';

// Dynamic import để tránh SSR issues với Plotly
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] flex items-center justify-center text-gray-500">
      Đang tải biểu đồ...
    </div>
  ),
});

interface ChartBlockProps {
  block: A2UIChartBlock;
}

export default function ChartBlock({ block }: ChartBlockProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
  }, [block]);

  if (!block.spec || !block.spec.data || !block.spec.layout) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        Lỗi: Biểu đồ không có dữ liệu hợp lệ
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
        Lỗi render biểu đồ: {error}
      </div>
    );
  }

  try {
    return (
      <div className="mb-4">
        {block.title && (
          <div className="font-semibold text-gray-800 mb-2">
            {block.title}
          </div>
        )}
        <div className="bg-white p-3 rounded-lg border border-gray-200">
          <Plot
            data={block.spec.data}
            layout={{
              ...block.spec.layout,
              autosize: true,
              responsive: true,
            }}
            config={{
              displayModeBar: true,
              responsive: true,
              ...block.spec.config,
            }}
            style={{ width: '100%', height: '400px' }}
            useResizeHandler={true}
            onError={(err: any) => {
              console.error('Plotly error:', err);
              setError(err?.message || 'Lỗi không xác định');
            }}
          />
        </div>
      </div>
    );
  } catch (err: any) {
    console.error('ChartBlock render error:', err);
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        Lỗi: {err?.message || 'Không thể render biểu đồ'}
      </div>
    );
  }
}

