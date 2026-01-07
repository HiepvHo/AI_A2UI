import type { A2UICardBlock } from '@/types/chatbot';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CardBlockProps {
  block: A2UICardBlock;
}

export default function CardBlock({ block }: CardBlockProps) {
  return (
    <Card 
      className="mb-3 border-l-4"
      style={{
        borderLeftColor: block.color,
      }}
    >
      <CardHeader className="pb-3">
        {block.icon && (
          <div className="text-2xl mb-2">{block.icon}</div>
        )}
        <CardTitle className="text-base">{block.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {block.description}
        </p>
      </CardContent>
    </Card>
  );
}

