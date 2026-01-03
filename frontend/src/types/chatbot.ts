// A2UI Block Types
export type A2UIBlockType = 'text' | 'card' | 'list' | 'chart' | 'button' | 'divider';

export type A2UITextStyle = 'normal' | 'heading' | 'subheading' | 'caption';

export interface A2UITextBlock {
  type: 'text';
  id: string;
  content: string;
  style: A2UITextStyle;
}

export interface A2UICardBlock {
  type: 'card';
  id: string;
  title: string;
  description: string;
  color: string;
  icon?: string;
}

export interface A2UIListBlock {
  type: 'list';
  id: string;
  title?: string;
  list_type: 'bullet' | 'numbered' | 'checkbox';
  items: string[];
}

export interface A2UIChartBlock {
  type: 'chart';
  id: string;
  chart_id: string;
  title?: string;
  spec: PlotlySpec;
}

export interface A2UIButtonBlock {
  type: 'button';
  id: string;
  label: string;
  action: string;
  style: 'primary' | 'secondary' | 'danger';
}

export interface A2UIDividerBlock {
  type: 'divider';
  id: string;
}

export type A2UIBlock =
  | A2UITextBlock
  | A2UICardBlock
  | A2UIListBlock
  | A2UIChartBlock
  | A2UIButtonBlock
  | A2UIDividerBlock;

// Plotly Types
export interface PlotlySpec {
  data: any[];
  layout: any;
  config?: any;
}

// API Types
export interface ChatRequest {
  query: string;
  session_id?: string;
  user_id?: number;
  context_limit?: number;
}

export interface Source {
  title?: string;
  source_file?: string;
  category?: string;
  relevance_score?: number;
  score?: number;
  content?: string;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  chart_spec?: PlotlySpec | null;
  chart_id?: string | null;
  a2ui_blocks: A2UIBlock[];
  sources: Source[];
  sql_query?: string | null;
  crisis_detected: boolean;
  context_used: boolean;
  query: string;
  session_id?: string | null;
  timestamp: string;
  processing_time?: number | null;
}

export interface Message {
  id: string;
  query: string;
  response: ChatResponse;
  timestamp: Date;
}

