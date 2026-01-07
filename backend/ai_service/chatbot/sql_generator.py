# -*- coding: utf-8 -*-
"""
SQL Generator - Emotion Chatbot
Chuyen natural language thanh SQL query cho emotion analytics
"""

from typing import Dict, Any, Optional, List
import json
import re
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from groq import Groq

logger = logging.getLogger(__name__)

from ...config.config import GROQ_API_KEY, LLM_MODEL, SQL_MAX_ROWS, SQL_TIMEOUT
from ...database.connection import async_session_maker


class SQLGenerator:
    """Generate SQL queries tu natural language su dung Groq (Llama 3.3 70B)"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.model = LLM_MODEL
        
        # Schema reference cho LLM
        self.schema_info = """
        DATABASE SCHEMA (PostgreSQL):
        
        1. emotion_topics (11 loại cảm xúc)
           - id: int (PRIMARY KEY)
           - name: varchar (anxiety, depression, anger, etc.)
           - name_vi: varchar (Lo âu, Trầm cảm, etc.)
           - icon, color: varchar
        
        2. emotion_logs (Nhật ký cảm xúc của user)
           - id: int (PRIMARY KEY)
           - user_id: int (FOREIGN KEY)
           - date: date
           - time: time
           - topic_id: int (NULLABLE, FOREIGN KEY)
           - emotion_labels: varchar[] (array tags: "buon", "vui", etc.)
           - intensity: int (1-5)
           - note: text
           - triggers: varchar[] (array)
           - crisis_level: int (0: normal, 1: mild, 2: moderate, 3: severe)
        
        3. mood_entries (Tâm trạng hàng ngày)
           - id: int (PRIMARY KEY)
           - user_id: int (FOREIGN KEY)
           - date: date
           - mood_score: int (1-10)
           - energy_level: int (1-10)
           - sleep_quality: int (1-10)
           - journal_text: text
           - grateful_for: text
        
        4. crisis_alerts (Cảnh báo khủng hoảng)
           - id: int (PRIMARY KEY)
           - user_id: int (FOREIGN KEY)
           - detected_at: timestamp
           - crisis_level: int
           - keywords_detected: varchar[]
           - message_content: text
           - is_resolved: bool
        
        5. users
           - id: int (PRIMARY KEY)
           - name: varchar
           - age: int
           - created_at: timestamp
        """
        
        self.system_prompt = """
        You are a SQL generator specialized in emotion analytics.
        
        TASK:
        - Convert Vietnamese questions into standard PostgreSQL SQL queries
        - Only SELECT queries, no INSERT/UPDATE/DELETE
        - Limit: LIMIT {max_rows}
        - Use JOIN when needed
        
        OUTPUT FORMAT (JSON):
        {{
            "sql": "SELECT ... FROM ... WHERE ...",
            "explanation": "Short user-friendly description in Vietnamese (NOT technical SQL details). Example: 'Phân tích cảm xúc 30 ngày qua' or 'Thống kê tâm trạng theo tuần'. DO NOT mention 'truy vấn', 'SQL', '1000 hàng', 'sắp xếp giảm dần' - use simple, natural language.",
            "chart_type": "bar|line|pie|scatter|table",
            "x_column": "x column name",
            "y_column": "y column name"
        }}
        
        CRITICAL - WHEN ANALYZING EMOTIONS:
        - ALWAYS select emotion_labels (array) and triggers (array) for specific emotion analysis
        - ALWAYS select topic_id and JOIN with emotion_topics to get emotion topic names
        - IMPORTANT: emotion_labels and triggers can be NULL or empty arrays []
        - For detailed emotion analysis, SELECT individual rows (don't use GROUP BY with array_agg)
        - Example: SELECT date, emotion_labels, triggers, topic_id, intensity, note FROM emotion_logs WHERE user_id = :user_id AND date >= ... ORDER BY date DESC
        - If you MUST use GROUP BY with array_agg, filter out NULL/empty arrays first:
          - Use: array_agg(DISTINCT emotion_labels) FILTER (WHERE emotion_labels IS NOT NULL AND array_length(emotion_labels, 1) > 0)
          - Or use: array_agg(DISTINCT unnest(emotion_labels)) FILTER (WHERE emotion_labels IS NOT NULL)
        - RECOMMENDED: For emotion analysis, select individual rows without GROUP BY to avoid array aggregation issues
        
        NOTES:
        - WHERE user_id = :user_id (always filter by user)
        - Use aggregates: COUNT, AVG, SUM when statistics are needed
        - Use DATE_TRUNC for time-based grouping
        - emotion_labels and triggers are arrays → use array_agg, unnest, ANY/ALL
        - When detailed emotion analysis is needed, SELECT individual rows with emotion_labels, triggers, topic_id
        """
    
    async def generate_sql(self, question: str, user_id: int = 1) -> Dict[str, Any]:
        """
        Generate SQL from natural language question
        
        Args:
            question: Cau hoi bang tieng Viet
            user_id: User ID de filter data
        
        Returns:
            Dict voi sql, explanation, chart_type, columns
        """
        try:
            prompt = f"""
            {self.system_prompt}
            
            DATABASE SCHEMA:
            {self.schema_info}
            
            USER QUESTION: {question}
            USER_ID: {user_id}
            MAX_ROWS: {SQL_MAX_ROWS}
            
            CRITICAL - EXPLANATION FIELD:
            - Write SHORT, USER-FRIENDLY description in Vietnamese (max 50 characters)
            - DO NOT use technical terms: "truy vấn", "SQL", "1000 hàng", "sắp xếp giảm dần", "giới hạn", "bản ghi"
            - Use natural language that end users understand
            - Examples:
              * Good: "Phân tích cảm xúc 30 ngày qua"
              * Good: "Thống kê tâm trạng theo tuần"
              * Bad: "Truy vấn SQL lấy dữ liệu cảm xúc, giới hạn 1000 hàng"
            
            Hãy tạo SQL query phù hợp và trả JSON theo format trên.
            """
            
            logger.debug(f"Generating SQL: user_id={user_id}")
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )
            response_text = response.choices[0].message.content.strip()
            
            # Trich xuat JSON (co the co markdown fence)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Xoa control characters lam hong JSON parsing
                # Chi xoa cac control characters khong hop le (giu \n, \t, \r vi hop le trong JSON strings)
                # Xoa: \x00-\x08 (tru \n), \x0b-\x0c, \x0e-\x1f, \x7f-\x9f
                json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
                
                # Sua backslash escapes: LLM co the dung \ o cuoi dong SQL (line continuation)
                # Trong JSON string, \ can escape thanh \\, nhung \ o cuoi dong thi can xoa hoac escape
                # Pattern: \ o cuoi dong (truoc newline) trong SQL string
                # Thay the: \ + newline → newline (xoa line continuation)
                json_str = re.sub(r'\\\s*\n\s*', ' ', json_str)
                
                # Thu sua cac van de JSON thuong gap: unescaped newlines trong strings
                # Thay the unescaped newlines trong string values bang escaped newlines
                json_str = re.sub(r'(?<!\\)\n(?![\\"])', '\\n', json_str)
                
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Thu them lan nua voi cleaning manh hon
                    # Xoa tat ca backslashes o cuoi dong va normalize whitespace
                    json_str_clean = json_str.replace('\\\n', ' ').replace('\\\r', ' ')
                    json_str_clean = json_str_clean.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    json_str_clean = re.sub(r'\s+', ' ', json_str_clean)  # Normalize whitespace
                    try:
                        result = json.loads(json_str_clean)
                        logger.debug("JSON parsed after cleaning")
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error: {str(e)}")
                        raise ValueError(f"LLM tra ve JSON khong hop le: {str(e)}")
            else:
                raise ValueError("LLM khong tra ve JSON hop le")
            
            # Xac thuc ket qua
            if 'sql' not in result:
                raise ValueError("Missing 'sql' field in LLM response")
            
            # Thay the placeholders
            sql = result['sql']
            sql = sql.replace(':user_id', str(user_id))
            sql = sql.replace(':max_rows', str(SQL_MAX_ROWS))
            result['sql'] = sql
            
            logger.debug(f"Generated SQL: {result.get('chart_type')}")
            
            return {
                'success': True,
                'sql': sql,
                'explanation': result.get('explanation', ''),
                'chart_type': result.get('chart_type', 'table'),
                'x_column': result.get('x_column'),
                'y_column': result.get('y_column')
            }
            
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            return {
                'success': False,
                'error': f"Loi generate SQL: {str(e)}",
                'sql': None
            }
    
    async def execute_sql(self, sql: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Execute SQL query va tra ve results
        
        Args:
            sql: SQL query string
            session: AsyncSession tu database
        
        Returns:
            Dict voi data (list of dict) hoac error
        """
        try:
            logger.debug("Executing SQL")
            # Bao mat: Chi cho phep SELECT
            if not sql.strip().upper().startswith('SELECT'):
                logger.warning("Non-SELECT query rejected")
                return {
                    'success': False,
                    'error': "Chi cho phep SELECT queries"
                }
            
            # Thuc thi
            result = await session.execute(text(sql))
            rows = result.fetchall()
            
            # Chuyen thanh list of dict
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = []
            
            logger.debug(f"SQL executed: {len(data)} rows")
            return {
                'success': True,
                'data': data,
                'row_count': len(data)
            }
            
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            return {
                'success': False,
                'error': f"Loi execute SQL: {str(e)}",
                'data': []
            }
    
    async def get_data_range(self, user_id: int = 1) -> Dict[str, Any]:
        """
        Query min/max date và row count từ emotion_logs để biết data range thực tế
        
        Args:
            user_id: User ID
        
        Returns:
            Dict với min_date, max_date, total_rows
        """
        try:
            async with async_session_maker() as session:
                query = text("""
                    SELECT 
                        MIN(date) as min_date,
                        MAX(date) as max_date,
                        COUNT(*) as total_rows
                    FROM emotion_logs
                    WHERE user_id = :user_id
                """)
                result = await session.execute(query, {"user_id": user_id})
                row = result.fetchone()
                
                if row and row[0]:  # Có data
                    return {
                        'success': True,
                        'min_date': str(row[0]) if row[0] else None,
                        'max_date': str(row[1]) if row[1] else None,
                        'total_rows': row[2] if row[2] else 0
                    }
                else:
                    return {
                        'success': True,
                        'min_date': None,
                        'max_date': None,
                        'total_rows': 0
                    }
        except Exception as e:
            logger.error(f"Error getting data range: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def text_to_data(self, question: str, user_id: int = 1) -> Dict[str, Any]:
        """
        End-to-end: question → SQL → data
        
        Args:
            question: User question
            user_id: User ID
        
        Returns:
            Dict voi sql, data, chart_type, explanation, data_range (nếu 0 rows)
        """
        # Buoc 1: Generate SQL
        sql_result = await self.generate_sql(question, user_id)
        
        if not sql_result['success']:
            return sql_result
        
        # Buoc 2: Execute SQL
        async with async_session_maker() as session:
            exec_result = await self.execute_sql(sql_result['sql'], session)
        
        if not exec_result['success']:
            return {
                'success': False,
                'error': exec_result['error'],
                'sql': sql_result['sql']
            }
        
        # Buoc 3: Neu khong co data, lay data range de LLM biet data co tu ngay nao
        data_range = None
        if exec_result['row_count'] == 0:
            data_range = await self.get_data_range(user_id)
            logger.debug(f"No data found: {data_range}")
        
        # Buoc 4: Ket hop ket qua
        result = {
            'success': True,
            'sql': sql_result['sql'],
            'explanation': sql_result['explanation'],
            'data': exec_result['data'],
            'row_count': exec_result['row_count'],
            'chart_type': sql_result['chart_type'],
            'x_column': sql_result['x_column'],
            'y_column': sql_result['y_column']
        }
        
        if data_range:
            result['data_range'] = data_range
        
        return result


# Global instance
_sql_generator = None

async def get_sql_generator() -> SQLGenerator:
    """Get or create global SQL generator instance"""
    global _sql_generator
    
    if _sql_generator is None:
        _sql_generator = SQLGenerator()
    
    return _sql_generator

