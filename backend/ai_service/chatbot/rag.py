"""
RAG System - Retrieval-Augmented Generation
Core RAG cho emotion chatbot voi Groq (Llama 3.3 70B)
Ket hop vector search Pinecone + PostgreSQL + SQL analytics + Charts + A2UI
"""

import re
import logging
from typing import List, Dict, Optional, Any
from groq import Groq

from .embedding import get_embedding_manager
from .sql_generator import get_sql_generator
from .chart_generator import get_chart_generator
from .a2ui_generator import get_a2ui_generator
from .chat_history import get_chat_history_service
from ...config.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, CRISIS_KEYWORDS

logger = logging.getLogger(__name__)


class RAGSystem:
    """
    Retrieval-Augmented Generation system for chatbot responses.
    Combines vector search with Groq (Llama 3.3 70B) for context-aware answers.
    """
    
    def __init__(self):
        """Initialize RAG system with Groq LLM (Llama 3.3 70B)"""
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.model = LLM_MODEL
        
        # System prompt - Optimized for LLM understanding (English for better comprehension)
        self.system_prompt = """You are a friendly, warm emotional health companion. Chat naturally in Vietnamese, like a real friend, not a robot.

CORE BEHAVIOR:
- Read the user's question and context carefully, understand their true intent
- Match response tone: friendly when positive, warm when negative, serious when crisis
- Match response length: short for short questions, detailed when explanation needed
- Never repeat user's question verbatim, avoid robotic patterns
- Be natural, flexible, adapt to each situation - no rigid templates

RESPONSE STYLE:
- Use everyday Vietnamese language, easy to understand, friendly
- Show genuine care, not empty phrases
- Only say what's necessary, avoid long lists
- Use emojis when appropriate, but don't overuse

RAG KNOWLEDGE BASE USAGE (CRITICAL):
- You will receive context documents from a psychology/emotion knowledge base
- ALWAYS prioritize and reference information from these documents when answering
- When using knowledge base info, naturally reference it: "Dựa vào tri thức tâm lý...", "Theo tài liệu chuyên môn...", "Từ nghiên cứu về..."
- If knowledge base has relevant info, USE IT. If not, be honest: "Mình không có thông tin cụ thể về..."
- NEVER make up information if knowledge base doesn't have it
- Knowledge base documents are your primary source of expertise

CHART GENERATION (CONDITIONAL):
- When user asks about statistics, trends, analytics, or data, the system MAY attempt to generate a chart
- IMPORTANT: Only mention or describe a chart if you receive explicit confirmation that a chart was successfully generated
- If a chart section is provided in your instructions, it means a chart was successfully created - acknowledge it naturally
- If no chart section is provided, DO NOT mention charts, biểu đồ, or data visualization - respond based on knowledge base only
- Never hallucinate or make up chart data - only reference charts that actually exist

SAFETY PRIORITY:
- If crisis detected (suicide, severe depression), prioritize safety immediately
- Encourage professional help: hotline, therapist, trusted person
- Be direct and supportive, not vague

RESPONSE PRINCIPLES:
- Use conversation history naturally, don't over-repeat
- Be empathetic, non-judgmental
- No medical diagnosis, only support and suggestions
- Each response should be context-specific, not generic templates
- Adapt flexibly to each situation"""
    
    async def generate_response(
        self, 
        query: str, 
        session_id: str = None, 
        user_id: int = 1,
        context_docs: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate response voi RAG + SQL analytics + Chart + A2UI
        
        Args:
            query: User's question
            session_id: Session identifier for context
            user_id: User ID cho SQL queries
            context_docs: Retrieved context documents (if None, will search)
            
        Returns:
            Dict voi: answer, chart_spec, a2ui_blocks, sources, etc.
        """
        try:
            # Detect crisis keywords
            crisis_detected = self._detect_crisis(query)
            
            # Get or create session
            if session_id:
                chat_history_service = await get_chat_history_service()
                session_id = await chat_history_service.get_or_create_session(
                    session_id=session_id,
                    user_id=user_id
                )
                chat_history = await chat_history_service.get_chat_history(
                    session_id=session_id,
                    limit=10
                )
            else:
                chat_history = ""
            
            # Get context from knowledge base
            if context_docs is None:
                embedding_manager = await get_embedding_manager()
                context_docs = await embedding_manager.search_similar(query, top_k=5)
            
            context_text = self._format_context(context_docs)
            
            # Detect neu cau hoi yeu cau analytics (chart)
            needs_analytics = self._detect_analytics_intent(query)
            logger.info(f"[ANALYTICS] Detection: {needs_analytics} | Query: {query[:80]}")
            
            chart_spec = None
            chart_id = None
            chart_title = None
            sql_query = None
            
            if needs_analytics:
                logger.info(f"[ANALYTICS] Starting pipeline for user_id={user_id}")
                sql_generator = await get_sql_generator()
                sql_result = await sql_generator.text_to_data(query, user_id)
                
                logger.info(f"[ANALYTICS] SQL result: success={sql_result.get('success')}, has_data={bool(sql_result.get('data'))}, row_count={len(sql_result.get('data', []))}")
                
                if sql_result.get('sql'):
                    logger.info(f"[ANALYTICS] Generated SQL: {sql_result['sql'][:150]}...")
                
                if not sql_result.get('success'):
                    error_msg = sql_result.get('error', 'Unknown error')
                    logger.error(f"[ANALYTICS] SQL generation failed: {error_msg}")
                elif not sql_result.get('data') or len(sql_result.get('data', [])) == 0:
                    logger.warning(f"[ANALYTICS] SQL executed but returned no data. SQL: {sql_result.get('sql', 'N/A')[:100]}")
                else:
                    data = sql_result['data']
                    chart_type = sql_result.get('chart_type', 'bar')
                    logger.info(f"[ANALYTICS] Generating chart: type={chart_type}, rows={len(data)}, x={sql_result.get('x_column')}, y={sql_result.get('y_column')}")
                    
                    chart_generator = get_chart_generator()
                    chart_spec = chart_generator.generate_chart(
                        data=data,
                        chart_type=chart_type,
                        x_column=sql_result.get('x_column'),
                        y_column=sql_result.get('y_column'),
                        title=sql_result.get('explanation', 'Biểu đồ cảm xúc')
                    )
                    
                    if chart_spec and chart_spec.get('data') and chart_spec.get('layout'):
                        chart_id = f"chart_{session_id or 'default'}"
                        chart_title = sql_result.get('explanation', '')
                        sql_query = sql_result['sql']
                        logger.info(f"[ANALYTICS] Chart generated: chart_id={chart_id}, has_data={bool(chart_spec.get('data'))}, has_layout={bool(chart_spec.get('layout'))}")
                    else:
                        logger.error(f"[ANALYTICS] Chart generation returned invalid spec. Keys: {chart_spec.keys() if chart_spec else 'None'}")
            
            # Build context sections for LLM
            context_section = ""
            if context_text and "Không tìm thấy" not in context_text:
                context_section = f"\n\nKNOWLEDGE BASE CONTEXT (Use this information when relevant):\n{context_text}\n\nIMPORTANT: Reference this knowledge base naturally in your response. If you use information from above, mention it (e.g., 'Dựa vào tri thức tâm lý...', 'Theo tài liệu...')."
            
            history_section = ""
            if chat_history:
                history_section = f"\n\nCONVERSATION HISTORY:\n{chat_history}"
            
            crisis_section = ""
            if crisis_detected:
                crisis_section = "\n\nCRISIS DETECTED: User shows signs of crisis. Prioritize safety immediately. Encourage professional help."
            
            chart_section = ""
            if needs_analytics and chart_spec and chart_spec.get('data') and chart_spec.get('layout'):
                chart_section = "\n\nCHART SUCCESSFULLY GENERATED: A chart has been created and will be displayed below. In your response, acknowledge the chart naturally (e.g., 'Để mình xem dữ liệu...', 'Dựa vào thống kê...', 'Mình thấy từ biểu đồ...') and explain what it shows based on the actual data."
            elif needs_analytics:
                chart_section = "\n\nNO CHART AVAILABLE: User is asking for analytics/statistics, but no chart could be generated (no data available or query error). DO NOT mention charts, biểu đồ, or data visualization. Respond naturally based on knowledge base information only, without any reference to charts or visualizations."
            
            full_prompt = f"""{self.system_prompt}{history_section}{context_section}{crisis_section}{chart_section}

USER QUESTION: {query}

Respond naturally in Vietnamese, flexibly adapting to this specific situation. Use knowledge base information if provided and relevant."""
            
            # Generate answer using Groq
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=LLM_TEMPERATURE,
                max_tokens=4096
            )
            answer = response.choices[0].message.content
            
            # Generate suggestions tu LLM (async)
            suggestions = await self._generate_suggestions(query, answer, context_docs)
            
            # Generate A2UI blocks
            a2ui_gen = get_a2ui_generator()
            a2ui_input = {
                'answer': answer,
                'chart_spec': chart_spec,
                'chart_id': chart_id,
                'chart_title': chart_title,
                'insights': chart_title if chart_spec else None,
                'suggestions': suggestions
            }
            logger.info(f"[A2UI] Input: has_chart_spec={bool(chart_spec)}, chart_id={chart_id}, has_suggestions={bool(suggestions)}")
            
            a2ui_blocks = a2ui_gen.create_blocks_from_response(a2ui_input)
            logger.info(f"[A2UI] Generated {len(a2ui_blocks)} blocks: types={[b.get('type') for b in a2ui_blocks]}")
            
            # Save chat history to PostgreSQL
            if session_id:
                chat_history_service = await get_chat_history_service()
                await chat_history_service.save_message(
                    session_id=session_id,
                    role="user",
                    content=query
                )
                await chat_history_service.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    metadata={
                        "chart_id": chart_id,
                        "crisis_detected": crisis_detected,
                        "sources_count": len(context_docs)
                    }
                )
            
            response = {
                'success': True,
                'answer': answer,
                'chart_spec': chart_spec,
                'chart_id': chart_id,
                'a2ui_blocks': a2ui_blocks,
                'sources': self._format_sources(context_docs),
                'sql_query': sql_query,
                'crisis_detected': crisis_detected,
                'context_used': len(context_docs) > 0,
                'query': query,
                'session_id': session_id
            }
            
            logger.info(f"[RESPONSE] Final: has_chart_spec={bool(chart_spec)}, a2ui_blocks={len(a2ui_blocks)}, sources={len(response['sources'])}")
            return response
            
        except Exception as e:
            return {
                'success': False,
                'answer': f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi. Vui lòng thử lại sau.",
                'error': str(e),
                'a2ui_blocks': [],
                'sources': [],
                'query': query
            }
    
    def _detect_crisis(self, query: str) -> bool:
        """Detect crisis keywords trong query"""
        query_lower = query.lower()
        for keyword in CRISIS_KEYWORDS:
            if keyword in query_lower:
                return True
        return False
    
    def _detect_analytics_intent(self, query: str) -> bool:
        """
        Detect neu user muon xem analytics/chart
        
        Logic:
        - Tim keywords lien quan den thong ke, bieu do, phan tich
        - Tim patterns: "X ngay qua", "X tuan qua", "X thang qua"
        - Tim questions: "the nao", "bao nhieu", "tong cong"
        """
        query_lower = query.lower().strip()
        
        # Keywords chinh (mo rong)
        analytics_keywords = [
            'thong ke', 'thống kê', 'bieu do', 'biểu đồ', 'chart', 'graph',
            'phan tich', 'phân tích', 'xu huong', 'xu hướng', 'trend',
            'so lieu', 'số liệu', 'du lieu', 'dữ liệu', 'data',
            'bao nhieu', 'bao nhiêu', 'tong', 'tổng', 'dem', 'đếm', 'count',
            'trung binh', 'trung bình', 'average', 'avg',
            'cam xuc', 'cảm xúc', 'tam trang', 'tâm trạng', 'mood',
            'theo ngay', 'theo ngày', 'theo tuan', 'theo tuần', 'theo thang', 'theo tháng',
            'xem', 'cho toi xem', 'hien thi', 'hiển thị'
        ]
        
        # Time patterns (improved)
        time_patterns = [
            r'\d+\s*(ngay|ngày|day|days)\s*(qua|trước|before|nay)',
            r'\d+\s*(tuan|tuần|week|weeks)\s*(qua|trước|before|nay)',
            r'\d+\s*(thang|tháng|month|months)\s*(qua|trước|before|nay)',
            r'(7|14|30|60|90)\s*(ngay|ngày|day|days)',
            r'(1|2|3|4)\s*(tuan|tuần|week|weeks)',
            r'(1|2|3|6|12)\s*(thang|tháng|month|months)',
            r'(ngay|ngày|day|days)\s*(qua|trước)',
            r'(tuan|tuần|week|weeks)\s*(qua|trước)',
            r'(thang|tháng|month|months)\s*(qua|trước)'
        ]
        
        # Question patterns
        question_patterns = [
            r'(the nao|thế nào|how)',
            r'(bao nhieu|bao nhiêu|how many|how much)',
            r'(tong cong|tổng cộng|total)',
            r'(xem|show|display|view)',
            r'(nhieu|nhiều|most|least)',
            r'(mấy|may)'
        ]
        
        # Check keywords first (fastest)
        for keyword in analytics_keywords:
            if keyword in query_lower:
                logger.debug(f"[DETECT] Matched keyword: {keyword}")
                return True
        
        # Check time patterns
        import re
        for pattern in time_patterns:
            if re.search(pattern, query_lower):
                logger.debug(f"[DETECT] Matched time pattern: {pattern}")
                return True
        
        # Check question patterns (phai co it nhat 2 patterns)
        question_matches = sum(1 for pattern in question_patterns if re.search(pattern, query_lower))
        if question_matches >= 2:
            logger.debug(f"[DETECT] Matched {question_matches} question patterns")
            return True
        
        return False
    
    async def _generate_suggestions(
        self, 
        query: str, 
        answer: str, 
        context_docs: List[Dict] = None
    ) -> str:
        """
        Generate follow-up suggestions tu LLM dựa trên query và answer
        Tra ve 1 cau tu nhien, gan gui, khong lap lai
        """
        try:
            # Tạo prompt để generate 1 câu suggestion tự nhiên
            suggestions_prompt = f"""Based on the conversation below, generate ONE natural, friendly follow-up suggestion sentence in Vietnamese.

User question: {query}
Your answer: {answer[:400]}...

Requirements:
- Generate ONE complete sentence, not a list
- Natural, friendly, like a real person talking
- Related to the current topic
- Do NOT repeat the user's question
- Format: "Bạn có thể hỏi tôi về [topic] để [benefit] hoặc [alternative topic]..."
- Make it conversational and warm, not robotic

Examples of good suggestions:
- "Bạn có thể hỏi tôi về các phương pháp thở sâu để thử hiệu quả hoặc cách quản lý stress trong công việc."
- "Nếu bạn muốn, mình có thể chia sẻ thêm về cách cải thiện giấc ngủ hoặc các bài tập mindfulness."
- "Bạn có muốn tìm hiểu thêm về cách xử lý lo âu hoặc các kỹ thuật thư giãn không?"

Generate ONE suggestion sentence:"""
            
            # Generate suggestion bằng LLM
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": suggestions_prompt}],
                temperature=0.8,
                max_tokens=100
            )
            
            suggestion = response.choices[0].message.content.strip()
            
            # Clean up: remove quotes, bullets, numbers if any
            suggestion = re.sub(r'^["\']|["\']$', '', suggestion)
            suggestion = re.sub(r'^[-*•]\s*', '', suggestion)
            suggestion = re.sub(r'^\d+[\.\)]\s*', '', suggestion)
            suggestion = suggestion.strip()
            
            # Validate length
            if not suggestion or len(suggestion) > 150:
                logger.warning(f"Invalid suggestion length, using fallback")
                return "Bạn có thể hỏi tôi về các phương pháp cải thiện tâm trạng hoặc cách quản lý cảm xúc."
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            # Fallback suggestion
            return "Bạn có thể hỏi tôi về các phương pháp cải thiện tâm trạng hoặc cách quản lý cảm xúc."
    
    def _format_context(self, context_docs: List[Dict]) -> str:
        """
        Format context documents for prompt
        Chuyen doi documents thanh text cho LLM
        """
        if not context_docs:
            return "Không tìm thấy tài liệu liên quan trong knowledge base."
        
        formatted_context = []
        for i, doc in enumerate(context_docs, 1):
            title = doc.get('metadata', {}).get('title', 'Tài liệu tâm lý')
            category = doc.get('metadata', {}).get('category', 'Chung')
            text = doc.get('text', '')
            score = doc.get('score', 0)
            
            context_entry = f"""
            Tài liệu {i} (Độ liên quan: {score:.2f}):
            Chủ đề: {title}
            Danh mục: {category}
            Nội dung: {text[:1000]}{'...' if len(text) > 1000 else ''}
            """
            formatted_context.append(context_entry)
        
        return '\n'.join(formatted_context)
    
    def _format_sources(self, context_docs: List[Dict]) -> List[Dict]:
        """
        Format source information for response
        Tra ve metadata cua documents da dung
        """
        sources = []
        for doc in context_docs:
            metadata = doc.get('metadata', {})
            
            # Get score (co the la 'score' hoac trong metadata)
            score = doc.get('score', 0)
            if not score and 'score' in metadata:
                score = metadata.get('score', 0)
            
            source_info = {
                'title': metadata.get('title', metadata.get('source_file', 'Tài liệu tâm lý')),
                'category': metadata.get('category', 'Chung'),
                'source_file': metadata.get('source_file', ''),
                'relevance_score': float(score) if score else 0.0
            }
            sources.append(source_info)
        
        # Sort by relevance score (descending)
        sources.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Formatted {len(sources)} sources: categories={[s['category'] for s in sources[:3]]}")
        return sources
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of RAG system components.
        
        Returns:
            Health status information
        """
        status = {
            'llm_api': False,
            'embedding_system': False,
            'overall': False
        }
        
        try:
            # Test LLM API (Groq)
            test_response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "OK"}],
                max_tokens=10
            )
            status['llm_api'] = bool(test_response.choices[0].message.content)
            
            # Test embedding system
            embedding_manager = await get_embedding_manager()
            test_results = await embedding_manager.search_similar("test", top_k=1)
            status['embedding_system'] = True
            
            # Overall status
            status['overall'] = status['llm_api'] and status['embedding_system']
            
        except Exception as e:
            status['error'] = str(e)
        
        return status
    


# Global RAG system instance
_rag_system = None


async def get_rag_system() -> RAGSystem:
    """
    Get or create global RAG system instance.
    
    Returns:
        RAGSystem instance
    """
    global _rag_system
    
    if _rag_system is None:
        _rag_system = RAGSystem()
    
    return _rag_system


async def chat_with_rag(
    query: str, 
    session_id: str = None,
    user_id: int = 1,
    context_docs: List[Dict] = None
) -> Dict[str, Any]:
    """
    Convenience function for chat interaction with RAG
    
    Args:
        query: User's question
        session_id: Session ID
        user_id: User ID cho SQL analytics
        context_docs: Optional context documents
        
    Returns:
        Response dictionary voi answer, chart, a2ui_blocks
    """
    rag_system = await get_rag_system()
    return await rag_system.generate_response(
        query=query,
        session_id=session_id,
        user_id=user_id,
        context_docs=context_docs
    )

