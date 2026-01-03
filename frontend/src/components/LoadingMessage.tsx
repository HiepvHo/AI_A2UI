export default function LoadingMessage() {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%] bg-white px-4 py-3 rounded-xl border border-gray-200">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0s' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
          </div>
          <span className="text-sm text-gray-500 ml-2">Đang suy nghĩ...</span>
        </div>
      </div>
    </div>
  );
}

