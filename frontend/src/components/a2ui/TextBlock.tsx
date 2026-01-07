import type { A2UITextBlock } from '@/types/chatbot';

interface TextBlockProps {
  block: A2UITextBlock;
}

export default function TextBlock({ block }: TextBlockProps) {
  const getTextClasses = () => {
    switch (block.style) {
      case 'heading':
        return 'text-xl font-bold text-[#E6ECF5] mb-2';
      case 'subheading':
        return 'text-lg font-semibold text-[#C9D1E3] mb-2';
      case 'caption':
        return 'text-sm text-[#8B94A7]';
      default:
        return 'text-base text-[#E6ECF5] whitespace-pre-wrap';
    }
  };

  return (
    <p className={getTextClasses()}>
      {block.content}
    </p>
  );
}

