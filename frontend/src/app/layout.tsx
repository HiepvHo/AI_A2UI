import type React from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Emotion Chatbot - Hỗ trợ sức khỏe cảm xúc",
  description: "Chatbot AI hỗ trợ sức khỏe cảm xúc với RAG, phân tích thống kê và biểu đồ tương tác",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
