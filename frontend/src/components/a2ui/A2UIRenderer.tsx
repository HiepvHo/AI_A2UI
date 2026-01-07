'use client';

import type { A2UIBlock } from '@/types/chatbot';
import TextBlock from './TextBlock';
import CardBlock from './CardBlock';
import ListBlock from './ListBlock';
import InteractiveChartBlock from './InteractiveChartBlock';
import ButtonBlock from './ButtonBlock';
import DividerBlock from './DividerBlock';

interface A2UIRendererProps {
  blocks: A2UIBlock[];
  onButtonClick?: (action: string) => void;
}

export default function A2UIRenderer({ blocks, onButtonClick }: A2UIRendererProps) {
  const renderBlock = (block: A2UIBlock, index: number) => {
    switch (block.type) {
      case 'text':
        return <TextBlock key={block.id || index} block={block} />;
      case 'card':
        return <CardBlock key={block.id || index} block={block} />;
      case 'list':
        return <ListBlock key={block.id || index} block={block} />;
      case 'chart':
        return <InteractiveChartBlock key={block.id || index} block={block} />;
      case 'button':
        return (
          <ButtonBlock
            key={block.id || index}
            block={block}
            onClick={onButtonClick}
          />
        );
      case 'divider':
        return <DividerBlock key={block.id || index} />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-2">
      {blocks.map((block, index) => renderBlock(block, index))}
    </div>
  );
}

