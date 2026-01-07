import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

export default function LoadingMessage() {
  return (
    <div className="flex justify-start mb-4">
      <Card className="max-w-[85%]">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Đang suy nghĩ...</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

