/**
 * Utility functions to format Vietnamese text from database
 * Database stores text without diacritics, we need to format them for display
 * 
 * Mapping được tạo từ TẤT CẢ các giá trị thực tế trong DB (query từ emotion_logs và emotion_topics)
 */

// Mapping từ text không dấu sang có dấu - TẤT CẢ emotions từ DB
const EMOTION_MAPPING: Record<string, string> = {
  'binh thuong': 'Bình thường',
  'buc': 'Bực',
  'buon': 'Buồn',
  'gian': 'Giận',
  'hanh phuc': 'Hạnh phúc',
  'lo': 'Lo',
  'lo au': 'Lo âu',
  'met moi': 'Mệt mỏi',
  'nang dong': 'Năng động',
  'stress': 'Stress',
  'tu tin': 'Tự tin',
  'vui': 'Vui',
};

// Mapping triggers - TẤT CẢ triggers từ DB
const TRIGGER_MAPPING: Record<string, string> = {
  'cong viec': 'Công việc',
  'gia dinh': 'Gia đình',
};

// Mapping topic names - TẤT CẢ topics từ emotion_topics.name_vi
const TOPIC_MAPPING: Record<string, string> = {
  'Dong luc': 'Động lực',
  'Giac ngu': 'Giấc ngủ',
  'Khac': 'Khác',
  'Lo au': 'Lo âu',
  'Mat mat': 'Mất mát',
  'Quan he': 'Quan hệ',
  'Stress cong viec': 'Stress công việc',
  'Stress thi cu': 'Stress thi cử',
  'Thai nghen': 'Thai nghén',
  'Tram cam': 'Trầm cảm',
  'Tu tin': 'Tự tin',
};

/**
 * Format emotion label từ DB (không dấu) sang hiển thị (có dấu)
 */
export function formatEmotion(emotion: string): string {
  if (!emotion) return emotion;
  const lower = emotion.toLowerCase().trim();
  return EMOTION_MAPPING[lower] || capitalizeFirst(emotion);
}

/**
 * Format trigger từ DB (không dấu) sang hiển thị (có dấu)
 */
export function formatTrigger(trigger: string): string {
  if (!trigger) return trigger;
  const lower = trigger.toLowerCase().trim();
  return TRIGGER_MAPPING[lower] || capitalizeFirst(trigger);
}

/**
 * Format topic name từ DB sang hiển thị
 */
export function formatTopic(topic: string): string {
  if (!topic) return topic;
  return TOPIC_MAPPING[topic] || topic;
}

/**
 * Capitalize first letter of each word
 */
function capitalizeFirst(text: string): string {
  return text
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

