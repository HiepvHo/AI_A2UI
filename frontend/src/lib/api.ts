import type {
  ChatRequest,
  ChatResponse,
  AnalyticsSummaryResponse,
  ExplainChartRequest,
  ExplainChartResponse,
  EmotionOptionsResponse,
} from '@/types/chatbot';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chatbot/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

export function getSessionId(): string {
  // This function should only be called on client side
  if (typeof window === 'undefined') {
    return '';
  }
  
  try {
    let sessionId = localStorage.getItem('chatbot_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('chatbot_session_id', sessionId);
    }
    return sessionId;
  } catch (error) {
    // Fallback if localStorage is not available
    console.warn('localStorage not available:', error);
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export async function fetchAnalyticsSummary(params: {
  user_id: number;
  date_from?: string;
  date_to?: string;
  emotion?: string;
  trigger?: string;
  topic_id?: number;
}): Promise<AnalyticsSummaryResponse> {
  const query = new URLSearchParams();
  query.append('user_id', String(params.user_id));
  if (params.date_from) query.append('date_from', params.date_from);
  if (params.date_to) query.append('date_to', params.date_to);
  if (params.emotion) query.append('emotion', params.emotion);
  if (params.trigger) query.append('trigger', params.trigger);
  if (params.topic_id !== undefined) query.append('topic_id', String(params.topic_id));

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analytics/summary?${query.toString()}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

export async function fetchEmotionOptions(user_id: number): Promise<EmotionOptionsResponse> {
  const query = new URLSearchParams();
  query.append('user_id', String(user_id));

  const response = await fetch(`${API_BASE_URL}/api/v1/analytics/emotions?${query.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

export async function explainChartSelection(
  request: ExplainChartRequest
): Promise<ExplainChartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analytics/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

