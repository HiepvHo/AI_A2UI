import type { A2UIButtonBlock } from '@/types/chatbot';

interface ButtonBlockProps {
  block: A2UIButtonBlock;
  onClick?: (action: string) => void;
}

export default function ButtonBlock({ block, onClick }: ButtonBlockProps) {
  const getButtonClasses = () => {
    const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-opacity hover:opacity-80';
    switch (block.style) {
      case 'primary':
        return `${baseClasses} bg-blue-600 text-white`;
      case 'danger':
        return `${baseClasses} bg-red-600 text-white`;
      default:
        return `${baseClasses} bg-gray-200 text-gray-800`;
    }
  };

  const handleClick = () => {
    if (onClick) {
      onClick(block.action);
    }
  };

  return (
    <button
      className={getButtonClasses()}
      onClick={handleClick}
    >
      {block.label}
    </button>
  );
}

