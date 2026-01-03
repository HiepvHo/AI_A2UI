import type { A2UIListBlock } from '@/types/chatbot';

interface ListBlockProps {
  block: A2UIListBlock;
}

export default function ListBlock({ block }: ListBlockProps) {
  const ListTag = block.list_type === 'numbered' ? 'ol' : 'ul';
  const listClasses = block.list_type === 'numbered' 
    ? 'list-decimal list-inside' 
    : 'list-disc list-inside';

  return (
    <div className="mb-3">
      {block.title && (
        <div className="font-semibold text-gray-800 mb-2">
          {block.title}
        </div>
      )}
      <ListTag className={`${listClasses} text-gray-700 space-y-1`}>
        {block.items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ListTag>
    </div>
  );
}

