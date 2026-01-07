'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, X, Calendar, TrendingUp, Brain } from 'lucide-react';
import type { AnalyticsRecord, ExplainChartRequest, ExplainChartResponse } from '@/types/chatbot';
import { explainChartSelection } from '@/lib/api';
import { formatEmotion, formatTrigger, formatTopic } from '@/lib/textFormatter';

interface ChartDetailPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedData: AnalyticsRecord[];
  filters: ExplainChartRequest;
}

export default function ChartDetailPanel({
  isOpen,
  onClose,
  selectedData,
  filters,
}: ChartDetailPanelProps) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear explanation khi selectedData hoặc filters thay đổi (chọn ngày mới)
  useEffect(() => {
    setExplanation(null);
    setError(null);
  }, [selectedData, filters.point_date]);

  const handleExplain = async () => {
    setExplaining(true);
    setError(null);
    try {
      const response = await explainChartSelection(filters);
      setExplanation(response.explanation);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
      setError(msg);
    } finally {
      setExplaining(false);
    }
  };

  if (!isOpen) return null;

  // Tính toán thống kê nhanh
  const avgIntensity = selectedData.length > 0
    ? (selectedData.reduce((sum, r) => sum + (r.intensity || 0), 0) / selectedData.length).toFixed(1)
    : '0';
  const uniqueEmotions = new Set(selectedData.flatMap(r => r.emotion_labels || []));
  const uniqueTriggers = new Set(selectedData.flatMap(r => r.triggers || []));

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b bg-gradient-to-r from-primary/5 to-primary/10">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <CardTitle className="text-xl">Chi tiết dữ liệu</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-muted/50 rounded-lg p-3 border">
              <div className="text-xs text-muted-foreground mb-1">Số bản ghi</div>
              <div className="text-2xl font-bold">{selectedData.length}</div>
            </div>
            <div className="bg-muted/50 rounded-lg p-3 border">
              <div className="text-xs text-muted-foreground mb-1">Mức độ cảm xúc TB</div>
              <div className="text-2xl font-bold">{avgIntensity}/5</div>
            </div>
            <div className="bg-muted/50 rounded-lg p-3 border">
              <div className="text-xs text-muted-foreground mb-1">Ngày</div>
              <div className="text-sm font-semibold">{filters.point_date || selectedData[0]?.date || '-'}</div>
            </div>
          </div>

          {/* Data Table - Improved */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Dữ liệu chi tiết
              </h3>
              {selectedData.length > 20 && (
                <span className="text-xs text-muted-foreground">
                  Hiển thị 20/{selectedData.length} bản ghi đầu tiên
                </span>
              )}
            </div>
            <div className="border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/80">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider">Ngày</th>
                      <th className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider">Cảm xúc</th>
                      <th className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider">Lý do</th>
                      <th className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider">Mức độ cảm xúc</th>
                      <th className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider">Chủ đề</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {selectedData.slice(0, 20).map((record, idx) => (
                      <tr key={idx} className="hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3 font-medium">{record.date || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {record.emotion_labels.length > 0 ? (
                              record.emotion_labels.map((em, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {formatEmotion(em)}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {record.triggers.length > 0 ? (
                              record.triggers.map((tr, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {formatTrigger(tr)}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {record.intensity ? (
                            <Badge variant={record.intensity >= 4 ? 'destructive' : record.intensity >= 3 ? 'default' : 'secondary'}>
                              {record.intensity}/5
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{record.topic_name ? formatTopic(record.topic_name) : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Explain Button - Improved */}
          <div>
            <Button
              onClick={handleExplain}
              disabled={explaining || selectedData.length === 0}
              className="w-full h-11 text-base font-medium"
              size="lg"
            >
              {explaining ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang phân tích...
                </>
              ) : (
                <>
                  <Brain className="mr-2 h-4 w-4" />
                  Giải thích phần này
                </>
              )}
            </Button>
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Explanation - Improved */}
          {explanation && (
            <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary" />
                  Phân tích
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground">{explanation}</p>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
