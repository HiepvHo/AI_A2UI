# Emotion Chatbot - AI RAG Chatbot với Analytics

Chatbot AI về cảm xúc với RAG (Retrieval-Augmented Generation), SQL analytics, và biểu đồ tương tác.

## Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Groq (Llama 3.3 70B)
- **Vector DB**: Pinecone
- **Database**: PostgreSQL
- **Embedding**: sentence-transformers (multilingual-e5-base)
- **Charts**: Plotly
- **Frontend**: HTML + JavaScript (test frontend)

## Cài đặt

### 1. Clone và cài dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env`:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=chatbot-docs-dev

# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5442/db_chatbotllm
DB_HOST=localhost
DB_PORT=5442
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=db_chatbotllm

# Embedding
EMBEDDING_MODEL=intfloat/multilingual-e5-base
EMBEDDING_DIMENSION=768
```

### 3. Khởi tạo Database

```bash
# Chạy PostgreSQL (Docker)
docker-compose up -d

# Khởi tạo database và seed data
python scripts/init_database.py
```

### 4. Index Documents

Đặt PDF/Word documents vào `knowledge_base/emotions/`, `knowledge_base/psychology/`, `knowledge_base/mindfulness/`, sau đó:

```bash
python scripts/index_documents.py
```

### 5. Chạy Server

```bash
python -m uvicorn backend.app:app --reload --port 8000
```

Server chạy tại: `http://localhost:8000`

### 6. Test Frontend

Mở `test_frontend.html` trong browser.

## Cấu trúc Project

```
AI_A2UI/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── config/
│   │   └── config.py          # Configuration
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── connection.py      # DB connection
│   ├── routers/
│   │   └── chatbot.py         # Chatbot API endpoints
│   └── ai_service/
│       └── chatbot/
│           ├── rag.py          # RAG system (core)
│           ├── embedding.py    # Embedding manager
│           ├── sql_generator.py # SQL generation
│           ├── chart_generator.py # Chart generation
│           ├── a2ui_generator.py # A2UI blocks
│           ├── chat_history.py # Chat history service
│           └── retrieval.py    # Vector search
├── knowledge_base/            # PDF/Word documents
│   ├── emotions/
│   ├── psychology/
│   └── mindfulness/
├── scripts/
│   ├── init_database.py       # Initialize DB
│   └── index_documents.py     # Index documents to Pinecone
├── test_frontend.html         # Test frontend
├── docker-compose.yml         # PostgreSQL setup
└── requirements.txt           # Dependencies
```

## API Endpoints

### POST `/api/v1/chatbot/chat`

Chat với chatbot.

**Request:**
```json
{
  "query": "thống kê cảm xúc của tôi 7 ngày qua",
  "session_id": "session_123",
  "user_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "answer": "...",
  "chart_spec": {...},  // Plotly chart spec (nếu có)
  "chart_id": "chart_...",
  "a2ui_blocks": [...], // A2UI JSON blocks
  "sources": [...],      // Knowledge base sources
  "sql_query": "...",    // SQL query (nếu có)
  "processing_time": 5.2
}
```

## Tính năng

- **RAG**: Tìm kiếm semantic trong knowledge base (PDF/Word)
- **SQL Analytics**: Tự động generate SQL và tạo biểu đồ từ database
- **Charts**: Plotly charts tương tác (bar, line, pie, scatter, table)
- **A2UI**: JSON blocks cho UI components
- **Chat History**: Lưu lịch sử chat trong PostgreSQL
- **Crisis Detection**: Phát hiện khủng hoảng cảm xúc

## Notes

- User ID hiện tại hardcode = 1 (cho testing)
- Chart chỉ được tạo khi user hỏi về analytics/statistics
- Knowledge base documents được chunk và embed vào Pinecone
