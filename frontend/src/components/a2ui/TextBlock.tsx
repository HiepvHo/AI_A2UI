import type { A2UITextBlock } from '@/types/chatbot';

interface TextBlockProps {
  block: A2UITextBlock;
}

export default function TextBlock({ block }: TextBlockProps) {
  const getTextClasses = () => {
    switch (block.style) {
      case 'heading':
        return 'text-xl font-bold text-gray-900 mb-2';
      case 'subheading':
        return 'text-lg font-semibold text-gray-800 mb-2';
      case 'caption':
        return 'text-sm text-gray-600';
      default:
        return 'text-base text-gray-800 whitespace-pre-wrap';
    }
  };

  return (
    <p className={getTextClasses()}>
      {block.content}
    </p>
  );
}

