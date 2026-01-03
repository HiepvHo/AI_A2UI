import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Emotion Chatbot
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Chatbot AI hỗ trợ sức khỏe cảm xúc với RAG, phân tích thống kê và biểu đồ tương tác
        </p>
        <Link
          href="/chat"
          className="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-semibold hover:bg-blue-700 transition-colors shadow-lg"
        >
          Bắt đầu trò chuyện
        </Link>
        <div className="mt-12 text-sm text-gray-500">
          <p>Powered by Groq Llama 3.3 70B + RAG + Plotly</p>
        </div>
      </div>
    </div>
  );
}

