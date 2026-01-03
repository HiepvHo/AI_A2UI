import type { A2UICardBlock } from '@/types/chatbot';

interface CardBlockProps {
  block: A2UICardBlock;
}

export default function CardBlock({ block }: CardBlockProps) {
  const bgColor = `${block.color}10`;
  const borderColor = block.color;

  return (
    <div
      className="rounded-lg p-4 border-l-4 mb-3"
      style={{
        borderLeftColor: borderColor,
        backgroundColor: bgColor,
      }}
    >
      {block.icon && (
        <div className="text-2xl mb-2">{block.icon}</div>
      )}
      <div className="font-semibold text-gray-800 mb-1">
        {block.title}
      </div>
      <div className="text-sm text-gray-700">
        {block.description}
      </div>
    </div>
  );
}

