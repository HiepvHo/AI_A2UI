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
        self.system_prompt = """You are a warm, caring emotional friend who listens and supports. Chat naturally in Vietnamese, like a close friend sharing feelings, NOT a robot or data analyst.

CORE BEHAVIOR:
- Be empathetic, warm, and genuine - like talking to a friend over coffee
- Show real care and understanding, not just information
- Match response tone: gentle and supportive when negative emotions, happy and encouraging when positive
- Keep responses conversational and natural - avoid sounding like a textbook or report
- Never sound robotic or mechanical - be human, be real

RESPONSE STYLE (CRITICAL):
- Use warm, friendly Vietnamese: "bạn có thể... nè", "cố gắng lên nhé", "mình hiểu bạn đang...", "đừng lo nhé"
- Show genuine empathy: "Mình thấy bạn đang...", "Chắc bạn cảm thấy...", "Mình hiểu..."
- Be encouraging: "Bạn làm tốt lắm", "Cố gắng lên nhé", "Mình tin bạn sẽ..."
- Avoid cold, technical language - NO "mức độ cường độ", NO excessive statistics
- When mentioning intensity/emotion strength, say "cảm xúc mạnh/nhẹ" or "bạn cảm thấy rất..." instead of numbers
- Keep it simple and heartfelt - focus on feelings, not data
- VERY IMPORTANT: Only start with a greeting like "Xin chào" when the user actually greets first (e.g. says "xin chào", "chào", "hello").
- If the user does NOT greet, go straight into the supportive content without any greeting sentence at the beginning.

RAG KNOWLEDGE BASE USAGE:
- You will receive context documents from psychology/emotion knowledge base
- Use this knowledge SPARINGLY and naturally - only when truly relevant
- When referencing knowledge, say it casually: "Mình có đọc về...", "Có nghiên cứu cho thấy..." - NOT "Dựa vào tri thức tâm lý" every time
- DON'T over-reference knowledge base - be a friend first, expert second
- If knowledge base has relevant info, weave it in naturally. If not, rely on empathy and common sense
- NEVER make up information

CHART/ANALYTICS HANDLING:
- When user asks about statistics/trends, the system MAY generate a chart
- If chart is generated, mention it briefly and naturally: "Để mình xem dữ liệu...", "Mình thấy từ biểu đồ..."
- Focus on WHAT the data MEANS for the user's feelings, NOT the numbers themselves
- Avoid listing dates, exact numbers, percentages - instead say "bạn có nhiều ngày cảm thấy...", "cảm xúc chủ yếu là..."
- If no chart, don't mention it - just respond as a caring friend

SAFETY PRIORITY:
- If crisis detected (suicide, severe depression), prioritize safety immediately
- Be direct, warm, and supportive - encourage professional help
- Show genuine concern, not just protocol

RESPONSE PRINCIPLES:
- Be a friend who listens and understands, not a data analyst
- Focus on emotions and feelings, not statistics
- Use warm, encouraging language
- Keep it natural and conversational
- Show empathy and care in every response"""
    
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
            logger.debug(f"Analytics detection: {needs_analytics}")
            
            chart_spec = None
            chart_id = None
            chart_title = None
            sql_query = None
            
            sql_result = None
            if needs_analytics:
                logger.debug(f"Analytics pipeline: user_id={user_id}")
                sql_generator = await get_sql_generator()
                sql_result = await sql_generator.text_to_data(query, user_id)
                
                logger.debug(f"SQL result: success={sql_result.get('success')}, rows={sql_result.get('row_count', 0)}")
                
                if sql_result.get('sql'):
                    logger.debug(f"Generated SQL: {sql_result['sql'][:100]}...")
                
                if not sql_result.get('success'):
                    error_msg = sql_result.get('error', 'Unknown error')
                    logger.error(f"SQL generation failed: {error_msg}")
                elif not sql_result.get('data') or sql_result.get('row_count', 0) == 0:
                    logger.warning(f"SQL returned no data")
                    # Không tạo chart nhưng vẫn giữ sql_result để truyền cho LLM
                else:
                    data = sql_result['data']
                    chart_type = sql_result.get('chart_type', 'bar')
                    logger.debug(f"Generating chart: type={chart_type}, rows={len(data)}")
                    
                    chart_generator = get_chart_generator()
                    # explanation từ SQL generator đã là user-friendly, dùng làm chart title
                    chart_title = sql_result.get('explanation', 'Biểu đồ cảm xúc')
                    chart_spec = chart_generator.generate_chart(
                        data=data,
                        chart_type=chart_type,
                        x_column=sql_result.get('x_column'),
                        y_column=sql_result.get('y_column'),
                        title=chart_title
                    )
                    
                    if chart_spec and chart_spec.get('data') and chart_spec.get('layout'):
                        chart_id = f"chart_{session_id or 'default'}"
                        sql_query = sql_result['sql']
                        logger.debug(f"Chart generated: {chart_id}")
                    else:
                        logger.error(f"Chart generation failed: invalid spec")
            
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
            
            # SQL Analytics Section - CRITICAL: Always include when analytics detected
            sql_analytics_section = ""
            if needs_analytics and sql_result:
                if sql_result.get('success') and sql_result.get('row_count', 0) > 0:
                    # Có data - phân tích cụ thể
                    data = sql_result.get('data', [])
                    row_count = sql_result.get('row_count', 0)
                    sql_query = sql_result.get('sql', '')
                    
                    # Format data sample cho LLM - Format tốt hơn để LLM dễ phân tích
                    data_sample = data[:20] if len(data) > 20 else data  # Lấy 20 rows để có đủ context
                    data_summary = f"Total rows: {row_count}"
                    if data_sample:
                        data_summary += f"\n\nDetailed data (first {len(data_sample)} rows):\n"
                        for i, row in enumerate(data_sample, 1):
                            # Format row để dễ đọc
                            row_str = f"Row {i}: "
                            if 'date' in row:
                                row_str += f"Date: {row['date']}, "
                            if 'emotion_labels' in row and row['emotion_labels']:
                                labels = row['emotion_labels'] if isinstance(row['emotion_labels'], list) else [row['emotion_labels']]
                                row_str += f"Cảm xúc: {', '.join(labels)}, "
                            if 'triggers' in row and row['triggers']:
                                triggers = row['triggers'] if isinstance(row['triggers'], list) else [row['triggers']]
                                row_str += f"Lý do: {', '.join(triggers)}, "
                            if 'intensity' in row:
                                intensity_desc = "rất nhẹ" if row['intensity'] <= 2 else "nhẹ" if row['intensity'] == 3 else "mạnh" if row['intensity'] == 4 else "rất mạnh"
                                row_str += f"Cảm xúc {intensity_desc} ({row['intensity']}/5), "
                            if 'topic_id' in row and row['topic_id']:
                                row_str += f"Topic ID: {row['topic_id']}, "
                            if 'note' in row and row['note']:
                                row_str += f"Note: {row['note'][:50]}..."
                            data_summary += row_str.rstrip(', ') + "\n"
                    
                    sql_analytics_section = f"""
SQL ANALYTICS RESULT (CRITICAL - You MUST analyze this actual data):
- SQL Query: {sql_query[:200]}...
- {data_summary}
- Chart type: {sql_result.get('chart_type', 'bar')}
- X column: {sql_result.get('x_column')}, Y column: {sql_result.get('y_column')}

IMPORTANT - UNDERSTAND USER'S FEELINGS (NOT JUST DATA):
1. EMOTION LABELS (emotion_labels): These are the user's actual feelings (e.g., "buon", "vui", "lo au", "stress", "gian")
   - Focus on WHAT the user felt, not just counting occurrences
   - Talk about emotions naturally: "bạn có nhiều ngày cảm thấy buồn", "mình thấy bạn có cảm xúc..."
   - Avoid listing exact numbers - say "nhiều ngày", "một số ngày", "thường xuyên"
   - Show empathy: "Chắc bạn đã trải qua những ngày khó khăn khi cảm thấy..."

2. TRIGGERS (triggers): These are reasons/causes for emotions (e.g., "cong viec", "gia dinh")
   - Help user understand WHY they felt certain emotions
   - Connect triggers to feelings naturally: "Có vẻ như công việc đã khiến bạn..."
   - Be understanding, not analytical: "Mình hiểu khi bạn gặp vấn đề về..."

3. EMOTION STRENGTH: This is how strong the feeling was (1-5, where 1=very mild, 5=very strong)
   - NEVER say "mức độ cường độ" or "intensity"
   - Instead say: "bạn cảm thấy rất mạnh", "cảm xúc khá nhẹ", "bạn cảm thấy rất..."
   - Focus on the feeling, not the number: "Bạn đã trải qua những cảm xúc mạnh mẽ"

4. TOPIC_ID: Emotion topic names (if available) - mention naturally if relevant

RESPONSE REQUIREMENTS (CRITICAL):
- Be a caring friend, NOT a data analyst
- Focus on understanding the user's emotional journey, not statistics
- Use warm, empathetic language: "Mình thấy bạn...", "Chắc bạn đã...", "Mình hiểu..."
- Avoid cold data language: NO "tỷ lệ", NO "thống kê", NO "dữ liệu cho thấy"
- Instead say: "Mình thấy bạn có nhiều ngày...", "Có vẻ như bạn thường cảm thấy...", "Mình nhận thấy..."
- Provide genuine emotional support and understanding
- Suggest improvements warmly: "Bạn có thể thử...", "Mình nghĩ bạn nên...", "Cố gắng lên nhé"
- Keep it conversational and heartfelt
- Respond in Vietnamese with natural, warm language
"""
                elif sql_result.get('success') and sql_result.get('row_count', 0) == 0:
                    # Không có data - giải thích rõ và đề xuất
                    sql_query = sql_result.get('sql', '')
                    data_range = sql_result.get('data_range', {})
                    
                    range_info = ""
                    if data_range and data_range.get('success'):
                        min_date = data_range.get('min_date')
                        max_date = data_range.get('max_date')
                        total_rows = data_range.get('total_rows', 0)
                        if min_date and max_date:
                            range_info = f"\n- Database có data từ {min_date} đến {max_date} (tổng {total_rows} bản ghi)"
                        elif total_rows == 0:
                            range_info = "\n- Database không có dữ liệu cảm xúc nào"
                    
                    sql_analytics_section = f"""
SQL ANALYTICS RESULT (CRITICAL):
- SQL Query executed: {sql_query[:200]}...
- Result: 0 rows returned (no data found for the requested time range)
{range_info}

IMPORTANT: 
- Tell the user clearly in Vietnamese that no data was found for their requested time range
- If data_range is provided, mention the actual date range available in database
- Suggest an alternative time range that matches available data
- DO NOT give generic responses about emotions - be specific about the data issue
- Example response in Vietnamese: "Mình không tìm thấy dữ liệu cảm xúc trong 7 ngày qua. Database của bạn có data từ [min_date] đến [max_date]. Bạn có muốn xem phân tích trong khoảng thời gian đó không?"
"""
                elif not sql_result.get('success'):
                    # SQL error
                    error_msg = sql_result.get('error', 'Unknown error')
                    sql_analytics_section = f"""
SQL ANALYTICS RESULT (ERROR):
- SQL generation/execution failed: {error_msg}
- Tell the user that analytics could not be performed due to a technical issue
- Suggest they try rephrasing their question or ask about a different time period
"""
            
            chart_section = ""
            if needs_analytics and chart_spec and chart_spec.get('data') and chart_spec.get('layout'):
                chart_section = "\n\nCHART SUCCESSFULLY GENERATED: A chart has been created and will be displayed below. In your response, mention it briefly and naturally (e.g., 'Để mình xem dữ liệu...', 'Mình thấy từ biểu đồ...'). Focus on WHAT the data MEANS for the user's feelings, NOT listing numbers or statistics. Be warm and empathetic, like a friend explaining what they see."
            elif needs_analytics and sql_result and sql_result.get('row_count', 0) == 0:
                chart_section = "\n\nNO CHART GENERATED: No data available for chart. Explain this warmly and suggest alternatives, like a caring friend would."
            
            full_prompt = f"""{self.system_prompt}{history_section}{context_section}{crisis_section}{sql_analytics_section}{chart_section}
            
            USER QUESTION: {query}
            
Respond naturally in Vietnamese, flexibly adapting to this specific situation. 
- If SQL ANALYTICS RESULT is provided, you MUST analyze the actual data (not generic responses)
- Use knowledge base information only as supplementary context
- Be specific with numbers, dates, and actual data values"""
            
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
            # Tạo câu chốt tổng kết cho câu hỏi của user dựa trên dữ liệu thực tế
            summary_insight = None
            if needs_analytics and sql_result:
                if sql_result.get('row_count', 0) > 0:
                    # Có data - tạo câu chốt tổng kết dựa trên dữ liệu thực tế
                    row_count = sql_result.get('row_count', 0)
                    data_sample = data[:30] if len(data) > 30 else data  # Lấy 30 rows để phân tích
                    # Tạo câu chốt tổng kết với phân tích thực tế
                    summary_insight = await self._generate_summary_insight(query, row_count, data_sample)
                else:
                    # Không có data
                    summary_insight = "Chưa có dữ liệu trong khoảng thời gian này"
            
            a2ui_input = {
                'answer': answer,
                'chart_spec': chart_spec,
                'chart_id': chart_id,
                'chart_title': chart_title,
                'insights': summary_insight,  # Câu chốt cho câu hỏi, không phải mô tả SQL
                'suggestions': suggestions,
                'user_query': query  # Thêm user query để có context
            }
            logger.debug(f"A2UI input: chart={bool(chart_spec)}, suggestions={bool(suggestions)}")
            
            a2ui_blocks = a2ui_gen.create_blocks_from_response(a2ui_input)
            logger.debug(f"A2UI: {len(a2ui_blocks)} blocks")
            
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
            
            logger.debug(f"Response: chart={bool(chart_spec)}, blocks={len(a2ui_blocks)}, sources={len(response['sources'])}")
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
                return True
        
        # Check time patterns
        import re
        for pattern in time_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check question patterns (phai co it nhat 2 patterns)
        question_matches = sum(1 for pattern in question_patterns if re.search(pattern, query_lower))
        if question_matches >= 2:
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
    
    async def _generate_summary_insight(self, query: str, row_count: int, data_sample: List[Dict]) -> str:
        """
        Generate câu chốt tổng kết cho câu hỏi của user dựa trên dữ liệu thực tế
        Format: "Cảm xúc X ngày qua của bạn cho thấy [phân tích]. Bạn nên [gợi ý]."
        """
        try:
            # Phân tích dữ liệu để tạo summary
            emotions_count = {}
            triggers_count = {}
            intensity_sum = 0
            intensity_count = 0
            negative_emotions = ['buon', 'lo', 'lo au', 'stress', 'gian', 'buc', 'tram cam', 'so hai']
            positive_emotions = ['vui', 'hanh phuc', 'tu tin', 'nang dong', 'yeu doi']
            
            for row in data_sample:
                # Đếm emotions
                if 'emotion_labels' in row and row['emotion_labels']:
                    labels = row['emotion_labels'] if isinstance(row['emotion_labels'], list) else [row['emotion_labels']]
                    for label in labels:
                        if label:
                            emotions_count[label] = emotions_count.get(label, 0) + 1
                
                # Đếm triggers
                if 'triggers' in row and row['triggers']:
                    triggers = row['triggers'] if isinstance(row['triggers'], list) else [row['triggers']]
                    for trigger in triggers:
                        if trigger:
                            triggers_count[trigger] = triggers_count.get(trigger, 0) + 1
                
                # Tính intensity trung bình
                if 'intensity' in row and row['intensity'] is not None:
                    intensity_sum += row['intensity']
                    intensity_count += 1
            
            # Tìm emotions và triggers phổ biến nhất
            top_emotions = sorted(emotions_count.items(), key=lambda x: x[1], reverse=True)[:3]
            top_triggers = sorted(triggers_count.items(), key=lambda x: x[1], reverse=True)[:2]
            avg_intensity = intensity_sum / intensity_count if intensity_count > 0 else 0
            
            # Phân loại cảm xúc chủ đạo
            negative_count = sum(emotions_count.get(em, 0) for em in negative_emotions)
            positive_count = sum(emotions_count.get(em, 0) for em in positive_emotions)
            
            # Tạo data summary cho LLM
            data_summary = f"Total records: {row_count}\n"
            if top_emotions:
                data_summary += f"Top emotions: {', '.join([f'{em}({count})' for em, count in top_emotions])}\n"
            if top_triggers:
                data_summary += f"Top triggers: {', '.join([f'{tr}({count})' for tr, count in top_triggers])}\n"
            if avg_intensity > 0:
                data_summary += f"Average intensity: {avg_intensity:.1f}/5\n"
            data_summary += f"Negative emotions: {negative_count}, Positive emotions: {positive_count}\n"
            
            prompt = f"""Based on the user's question and actual emotion data, generate ONE warm, empathetic summary sentence in Vietnamese that:
1. Shows understanding of the user's emotional journey
2. Uses warm, friendly language like a caring friend
3. Provides gentle encouragement

User question: {query}
Emotion patterns from data:
{data_summary}

Requirements:
- ONE complete sentence (max 150 characters)
- Warm, conversational Vietnamese - like a friend talking
- Use phrases like: "Mình thấy bạn...", "Có vẻ như bạn...", "Chắc bạn đã..."
- Focus on feelings, not numbers - avoid "tỷ lệ", "thống kê", exact counts
- Include gentle encouragement: "Cố gắng lên nhé", "Bạn có thể thử...", "Mình tin bạn sẽ..."
- Format: "Mình thấy [time period] bạn [emotional observation]. [Gentle encouragement]."
- Examples:
  * "Mình thấy 20 ngày qua bạn có nhiều ngày cảm thấy buồn và lo lắng, chủ yếu liên quan đến công việc. Cố gắng lên nhé, bạn có thể thử các cách thư giãn để giảm stress."
  * "Mình thấy 30 ngày qua bạn có sự cân bằng giữa cảm xúc tích cực và tiêu cực. Tiếp tục duy trì những điều mang lại niềm vui cho bạn nhé."

Generate ONE warm, empathetic summary sentence:"""
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=120
            )
            
            insight = response.choices[0].message.content.strip()
            # Clean up
            insight = re.sub(r'^["\']|["\']$', '', insight)
            insight = insight.strip()
            
            # Validate length và format
            if not insight or len(insight) > 200:
                # Fallback: tạo câu đơn giản dựa trên data
                if negative_count > positive_count:
                    trigger_text = f" liên quan đến {top_triggers[0][0]}" if top_triggers else ""
                    return f"Cảm xúc của bạn trong thời gian này cho thấy nhiều cảm xúc tiêu cực{trigger_text}. Bạn nên thử các kỹ thuật quản lý cảm xúc."
                elif positive_count > negative_count:
                    return f"Cảm xúc của bạn trong thời gian này khá tích cực. Bạn nên tiếp tục duy trì các hoạt động mang lại niềm vui."
                else:
                    return f"Cảm xúc của bạn trong thời gian này có sự cân bằng. Bạn nên chú ý đến các yếu tố ảnh hưởng đến tâm trạng."
            
            return insight
            
        except Exception as e:
            logger.error(f"Error generating summary insight: {str(e)}")
            # Fallback
            if "30 ngày" in query or "30 ngay" in query:
                return "Cảm xúc 30 ngày qua của bạn cho thấy các xu hướng cảm xúc đáng chú ý. Bạn nên tiếp tục theo dõi và quản lý cảm xúc của mình."
            elif "7 ngày" in query or "7 ngay" in query:
                return "Cảm xúc 7 ngày qua của bạn cho thấy các mô hình cảm xúc. Bạn nên chú ý đến các yếu tố ảnh hưởng đến tâm trạng."
            else:
                return "Cảm xúc của bạn cho thấy các xu hướng đáng chú ý. Bạn nên tiếp tục theo dõi và quản lý cảm xúc của mình."
    
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
        
        logger.debug(f"Formatted {len(sources)} sources")
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

