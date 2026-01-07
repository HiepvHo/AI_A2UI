# Setup Instructions - Phase 1: shadcn/ui + Lucide

## 1. Cài đặt Dependencies

```bash
cd frontend
npm install
```

Hoặc nếu dùng yarn:
```bash
yarn install
```

## 2. Kiểm tra Dependencies đã cài

Các packages cần có:
- `lucide-react` - Icons
- `framer-motion` - Animations (sẽ dùng ở Phase 3)
- `class-variance-authority` - Variant management
- `clsx` - Class name utility
- `tailwind-merge` - Merge Tailwind classes

## 3. Chạy Development Server

```bash
npm run dev
```

## 4. Kiểm tra

Mở browser: `http://localhost:3000/chat`

Giao diện sẽ có:
- ✅ Modern buttons với icons
- ✅ Cards với shadow và border
- ✅ Input fields với focus states
- ✅ Badges cho sources
- ✅ Alert components cho errors/crisis
- ✅ Lucide icons thay thế emoji

## Notes

- Tailwind config đã được setup với CSS variables cho theming
- shadcn/ui components đã được tạo trong `src/components/ui/`
- Tất cả components đã được update để dùng shadcn/ui

