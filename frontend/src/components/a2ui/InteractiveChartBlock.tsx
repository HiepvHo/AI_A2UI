'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import type { A2UIChartBlock, ExplainChartRequest, AnalyticsRecord } from '@/types/chatbot';
import { fetchAnalyticsSummary, fetchEmotionOptions } from '@/lib/api';
import ChartDetailPanel from './ChartDetailPanel';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { formatEmotion } from '@/lib/textFormatter';

const USER_ID = 1; // Hardcoded for testing

// Dynamic import để tránh SSR issues với Plotly
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] flex items-center justify-center text-gray-500">
      Đang tải biểu đồ...
    </div>
  ),
});

interface InteractiveChartBlockProps {
  block: A2UIChartBlock;
}

export default function InteractiveChartBlock({ block }: InteractiveChartBlockProps) {
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<any>(null); // Khởi tạo null để đợi loadChartData
  const [loading, setLoading] = useState(true); // Bắt đầu với loading = true
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Track initial load
  const plotRef = useRef<any>(null); // Ref để access Plotly instance

  // Filter state
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [emotion, setEmotion] = useState<string>('');
  const [emotionOptions, setEmotionOptions] = useState<string[]>([]);
  
  // Panel state
  const [panelOpen, setPanelOpen] = useState(false);
  const [selectedData, setSelectedData] = useState<AnalyticsRecord[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<ExplainChartRequest>({
    user_id: USER_ID,
  });

  useEffect(() => {
    setError(null);
  }, [block]);

  // Load emotion options from backend
  useEffect(() => {
    fetchEmotionOptions(USER_ID)
      .then((res) => setEmotionOptions(res.emotions || []))
      .catch((err) => console.error('Error loading emotion options', err));
  }, []);

  // Load chart data với filters (auto-load on change)
  const loadChartData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchAnalyticsSummary({
        user_id: USER_ID,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        emotion: emotion || undefined,
      });

      if (response.data && response.data.length > 0) {
        // Theme-ready chart data
        const palettePrimary = '#6EE7F9';
        const foreground = '#E6ECF5';
        const muted = '#8B94A7';
        const grid = 'rgba(148,163,184,0.15)';
        const bg = 'rgba(15,23,42,0.65)';

        const newChartData = {
          data: [
            {
              x: response.data.map((d) => d.date),
              y: response.data.map((d) => d.intensity),
              type: 'scatter',
              mode: 'lines+markers',
              line: { color: palettePrimary, shape: 'spline', smoothing: 0.6, width: 2 },
              marker: { color: palettePrimary, size: 7, line: { color: '#0F172A', width: 1 } },
              hovertemplate:
                '<b>%{y:.2f}</b><br>Ngày: %{x}<extra></extra>',
              name: 'Mức độ cảm xúc',
            },
          ],
          layout: {
            autosize: true,
            responsive: true,
            paper_bgcolor: bg,
            plot_bgcolor: bg,
            margin: { l: 50, r: 20, t: 40, b: 50 },
            font: { family: 'Inter, system-ui, -apple-system, sans-serif', color: foreground, size: 13 },
            title: {
              text: block.title || 'Phân tích cảm xúc',
              font: { size: 16, color: foreground, family: 'Inter, system-ui, -apple-system, sans-serif' },
              x: 0,
              xanchor: 'left',
            },
            hovermode: 'x unified',
            hoverlabel: {
              bgcolor: 'rgba(15,23,42,0.9)',
              bordercolor: palettePrimary,
              font: { color: foreground },
            },
            dragmode: 'pan',
            hoverdistance: 30,
            spikedistance: 30,
            xaxis: {
              title: { text: 'Ngày', font: { color: foreground } },
              tickfont: { color: foreground, size: 11 },
              gridcolor: grid,
              zerolinecolor: grid,
              linecolor: grid,
              tickformat: '%b %d',
              showspikes: true,
              spikemode: 'across',
              spikesnap: 'cursor',
              spikethickness: 1,
            },
            yaxis: {
              title: { text: 'Mức độ cảm xúc', font: { color: foreground } },
              tickfont: { color: foreground, size: 11 },
              gridcolor: grid,
              zerolinecolor: grid,
              linecolor: grid,
              rangemode: 'tozero',
              showspikes: true,
              spikemode: 'across',
              spikethickness: 1,
            },
            legend: {
              bgcolor: 'rgba(15,23,42,0.6)',
              bordercolor: 'rgba(148,163,184,0.25)',
              borderwidth: 1,
              font: { color: foreground },
            },
            transition: {
              duration: 400,
              easing: 'cubic-in-out',
            },
            ...block.spec.layout,
          },
          config: {
            displayModeBar: true,
            displaylogo: false,
            responsive: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            scrollZoom: true,
            doubleClick: 'reset',
            toImageButtonOptions: {
              format: 'png',
              filename: 'chart',
              height: 600,
              width: 1200,
              scale: 2,
              bgcolor: 'rgba(15,23,42,0)',
            },
            ...block.spec.config,
          },
        };
        setChartData(newChartData);
        setIsInitialLoad(false);
      } else {
        // Nếu không có data từ API, fallback về block.spec để chart vẫn render
        if (isInitialLoad && block.spec && block.spec.data) {
          setChartData(block.spec);
          setIsInitialLoad(false);
        } else {
          setError('Không có dữ liệu cho bộ lọc hiện tại');
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
      setError(msg);
      // Nếu lỗi ở initial load, fallback về block.spec để chart vẫn render
      if (isInitialLoad && block.spec && block.spec.data) {
        setChartData(block.spec);
        setIsInitialLoad(false);
      }
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, emotion, block.spec.layout, block.spec.config, block.title, block.spec, isInitialLoad]);

  useEffect(() => {
    loadChartData();
  }, [loadChartData]);

  // Handle Plotly click event - hoạt động với cả chart ban đầu và chart đã filter
  const handlePlotClick = useCallback(async (event: any) => {
    if (!event?.points || event.points.length === 0) return;
    
    const point = event.points[0];
    let clickedDate = point.x;
    
    // Normalize date format: có thể là string hoặc Date object
    if (clickedDate instanceof Date) {
      clickedDate = clickedDate.toISOString().split('T')[0];
    } else if (typeof clickedDate === 'string') {
      // Đảm bảo format YYYY-MM-DD (có thể là "2025-12-08" hoặc "2025-12-08T00:00:00")
      clickedDate = clickedDate.split('T')[0];
    } else {
      console.warn('Unexpected date format:', clickedDate, typeof clickedDate);
      return;
    }
    
    try {
      // Lấy data của ngày được click (không áp dụng emotion filter khi click để lấy tất cả data của ngày đó)
      const response = await fetchAnalyticsSummary({
        user_id: USER_ID,
        date_from: clickedDate,
        date_to: clickedDate,
      });
      
      setSelectedData(response.data);
      setSelectedFilters({
        user_id: USER_ID,
        point_date: clickedDate,
        emotion: emotion || undefined, // Giữ emotion filter nếu có để hiển thị trong panel
      });
      setPanelOpen(true);
    } catch (err) {
      console.error('Error fetching detail data:', err);
    }
  }, [emotion]);

  // Re-attach click handler khi handlePlotClick thay đổi hoặc chartData thay đổi
  useEffect(() => {
    if (plotRef.current?.el && chartData && chartData.data) {
      const graphDiv = plotRef.current.el;
      if (graphDiv && graphDiv.on) {
        // Remove old handler
        graphDiv.removeAllListeners('plotly_click');
        // Attach new handler
        graphDiv.on('plotly_click', handlePlotClick);
      }
    }
  }, [handlePlotClick, chartData]);


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
        {error}
      </div>
    );
  }

  try {
    return (
      <div className="mb-4">
        <div className="font-semibold text-[#E6ECF5] mb-2">
          {block.title || 'Phân tích cảm xúc 30 ngày qua'}
        </div>

        {/* Filter Controls - styled like reference (3 controls) */}
        <Card className="mb-3">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-foreground">Từ ngày</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="h-10"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-foreground">Đến ngày</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="h-10"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-foreground">Cảm xúc</label>
                <select
                  className="h-10 rounded-md border bg-background px-3 text-sm"
                  value={emotion}
                  onChange={(e) => setEmotion(e.target.value)}
                >
                  <option value="">Tất cả</option>
                  {emotionOptions.map((em) => (
                    <option key={em} value={em}>
                      {formatEmotion(em)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {loading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground mt-3">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang tải...
              </div>
            )}
          </CardContent>
        </Card>

        {/* Chart - chỉ render khi chartData đã được load */}
        {chartData && chartData.data && (
          <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800 shadow-inner">
            <Plot
              ref={plotRef}
              data={chartData.data}
              layout={{
                ...chartData.layout,
                autosize: true,
                responsive: true,
              }}
              config={{
                displayModeBar: true,
                responsive: true,
                ...chartData.config,
                locale: 'vi',
              }}
              style={{ width: '100%', height: '400px' }}
              useResizeHandler={true}
              onError={(err: any) => {
                console.error('Plotly error:', err);
                setError(err?.message || 'Lỗi không xác định');
              }}
              onInitialized={(figure: any, graphDiv: any) => {
                // Plotly đã initialized, attach click handler trực tiếp vào Plotly instance
                plotRef.current = { el: graphDiv };
                if (graphDiv && graphDiv.on) {
                  // Remove old handler nếu có
                  graphDiv.removeAllListeners('plotly_click');
                  // Attach new handler trực tiếp vào Plotly
                  graphDiv.on('plotly_click', handlePlotClick);
                }
              }}
              onUpdate={(figure: any, graphDiv: any) => {
                // Khi Plotly update, đảm bảo handler vẫn được attach
                if (graphDiv && graphDiv.on) {
                  graphDiv.removeAllListeners('plotly_click');
                  graphDiv.on('plotly_click', handlePlotClick);
                }
              }}
              onClick={handlePlotClick} // Backup handler qua React prop
            />
          </div>
        )}

        {/* Detail Panel */}
        <ChartDetailPanel
          isOpen={panelOpen}
          onClose={() => setPanelOpen(false)}
          selectedData={selectedData}
          filters={selectedFilters}
        />
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

