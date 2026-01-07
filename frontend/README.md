# Emotion Chatbot Frontend

Frontend cho Emotion Chatbot sử dụng Next.js, React, TypeScript, và Tailwind CSS.

## Tech Stack

- **Next.js 16.1.1** - React framework
- **React 19.2.3** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **react-plotly.js** - Interactive charts
- **A2UI Renderer** - Custom block-based UI system

## Cài đặt

```bash
cd frontend
npm install
```

## Chạy Development Server

```bash
npm run dev
```

Frontend chạy tại: `http://localhost:3000`

## Cấu trúc Project

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Homepage
│   │   ├── chat/
│   │   │   └── page.tsx        # Chat page
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── a2ui/               # A2UI renderer components
│   │   │   ├── A2UIRenderer.tsx
│   │   │   ├── TextBlock.tsx
│   │   │   ├── CardBlock.tsx
│   │   │   ├── ListBlock.tsx
│   │   │   ├── InteractiveChartBlock.tsx  # Interactive Plotly chart renderer
│   │   │   ├── ChartDetailPanel.tsx  # Chart detail panel
│   │   │   ├── ButtonBlock.tsx
│   │   │   └── DividerBlock.tsx
│   │   ├── ChatMessage.tsx     # Message component
│   │   ├── ChatInput.tsx       # Input component
│   │   └── LoadingMessage.tsx   # Loading indicator
│   ├── lib/
│   │   └── api.ts              # API client
│   └── types/
│       └── chatbot.ts          # TypeScript types
└── package.json
```

## Environment Variables

Tạo file `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Tính năng

- ✅ Chat interface với backend API
- ✅ A2UI block rendering (text, card, list, chart, button, divider)
- ✅ Plotly.js interactive charts
- ✅ Session management (localStorage)
- ✅ Loading states
- ✅ Error handling
- ✅ Crisis detection alerts
- ✅ Source citations

## A2UI Blocks

Frontend hỗ trợ 6 loại A2UI blocks:

1. **Text Block** - Text với styles (normal, heading, subheading, caption)
2. **Card Block** - Highlight box với title, description, color, icon
3. **List Block** - Bullet, numbered, hoặc checkbox lists
4. **Chart Block** - Plotly.js interactive charts
5. **Button Block** - Action buttons với styles (primary, secondary, danger)
6. **Divider Block** - Horizontal divider

## API Integration

Frontend gọi backend API tại:
- `POST /api/v1/chatbot/chat` - Chat endpoint

Request format:
```typescript
{
  query: string;
  session_id?: string;
  user_id?: number;
  context_limit?: number;
}
```

Response format:
```typescript
{
  success: boolean;
  answer: string;
  chart_spec?: PlotlySpec;
  a2ui_blocks: A2UIBlock[];
  sources: Source[];
  crisis_detected: boolean;
  processing_time?: number;
}
```

## Build

```bash
npm run build
npm start
```
