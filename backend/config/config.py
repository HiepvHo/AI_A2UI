"""
Emotion Chatbot Configuration
Cau hinh cho AI chatbot cam xuc voi Gemini + Pinecone + PostgreSQL
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== AI SERVICE ==========
# Groq API (Llama 3.3 70B)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is required in environment variables")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is required in environment variables")

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "emotion-chatbot-index")

# ========== EMBEDDING CONFIG ==========
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "8"))

# ========== RAG CONFIG ==========
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "1000"))

# ========== APP CONFIG ==========
APP_NAME = os.getenv("APP_NAME", "Emotion Chatbot API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# ========== EMOTION CONFIG ==========
# 11 emotion topics
EMOTION_TOPICS = [
    {"id": 1, "name": "anxiety", "name_vi": "Lo âu", "icon": "😰", "color": "#F59E0B"},
    {"id": 2, "name": "depression", "name_vi": "Trầm cảm", "icon": "😞", "color": "#6B7280"},
    {"id": 3, "name": "anger", "name_vi": "Tức giận", "icon": "😠", "color": "#EF4444"},
    {"id": 4, "name": "fear", "name_vi": "Sợ hãi", "icon": "😨", "color": "#8B5CF6"},
    {"id": 5, "name": "stress", "name_vi": "Stress", "icon": "😫", "color": "#F97316"},
    {"id": 6, "name": "loneliness", "name_vi": "Cô đơn", "icon": "😔", "color": "#0EA5E9"},
    {"id": 7, "name": "happiness", "name_vi": "Vui vẻ", "icon": "😊", "color": "#10B981"},
    {"id": 8, "name": "excitement", "name_vi": "Phấn khích", "icon": "🤩", "color": "#FBBF24"},
    {"id": 9, "name": "gratitude", "name_vi": "Biết ơn", "icon": "🙏", "color": "#EC4899"},
    {"id": 10, "name": "confusion", "name_vi": "Bối rối", "icon": "😕", "color": "#84CC16"},
    {"id": 11, "name": "burnout", "name_vi": "Kiệt sức", "icon": "😩", "color": "#DC2626"}
]

# Crisis levels
CRISIS_LEVELS = {
    0: {"name": "normal", "name_vi": "Bình thường", "color": "#10B981"},
    1: {"name": "mild", "name_vi": "Nhẹ", "color": "#FBBF24"},
    2: {"name": "moderate", "name_vi": "Trung bình", "color": "#F97316"},
    3: {"name": "severe", "name_vi": "Nghiêm trọng", "color": "#DC2626"}
}

# Crisis keywords (detect tu chat)
CRISIS_KEYWORDS = [
    "tu tu", "chet", "khong muon song", "bo cuoc", "ket thuc", 
    "het hy vong", "khong con y nghia", "rat toi", "khong chiu noi"
]

# ========== LLM CONFIG ==========
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq Llama 3.3 70B
LLM_TIMEOUT = 30  # seconds
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4096  # Max tokens per response

# ========== SQL CONFIG ==========
SQL_MAX_ROWS = 1000
SQL_TIMEOUT = 10  # seconds

# ========== CHART CONFIG ==========
CHART_DEFAULT_HEIGHT = 400
CHART_DEFAULT_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]