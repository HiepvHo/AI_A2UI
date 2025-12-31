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
        Bạn là SQL generator chuyên về emotion analytics.
        
        NHIỆM VỤ:
        - Chuyển câu hỏi tiếng Việt thành SQL query chuẩn PostgreSQL
        - Chỉ SELECT, không INSERT/UPDATE/DELETE
        - Giới hạn: LIMIT {max_rows}
        - Sử dụng JOIN khi cần
        
        OUTPUT FORMAT (JSON):
        {{
            "sql": "SELECT ... FROM ... WHERE ...",
            "explanation": "Giải thích query bằng tiếng Việt",
            "chart_type": "bar|line|pie|scatter|table",
            "x_column": "tên cột x",
            "y_column": "tên cột y"
        }}
        
        LƯU Ý:
        - WHERE user_id = :user_id (luôn filter theo user)
        - Dùng aggregate: COUNT, AVG, SUM khi cần thống kê
        - Dùng DATE_TRUNC cho group by time
        - emotion_labels và triggers là array → ANY/ALL
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
            
            Hãy tạo SQL query phù hợp và trả JSON theo format trên.
            """
            
            logger.info(f"Generating SQL for question: {question[:100]}, user_id={user_id}")
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM SQL response: {response_text[:300]}...")
            
            # Extract JSON (co the co markdown fence)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Clean control characters that break JSON parsing
                # Remove only truly invalid control characters (keep \n, \t, \r which are valid in JSON strings)
                # Remove: \x00-\x08 (except \n), \x0b-\x0c, \x0e-\x1f, \x7f-\x9f
                json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
                
                # Also try to fix common JSON issues: unescaped newlines in strings
                # Replace unescaped newlines in string values with escaped newlines
                # This is a simple approach - may need refinement
                json_str = re.sub(r'(?<!\\)\n(?![\\"])', '\\n', json_str)
                
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Try one more time with more aggressive cleaning
                    json_str_clean = json_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    json_str_clean = re.sub(r'\s+', ' ', json_str_clean)  # Normalize whitespace
                    try:
                        result = json.loads(json_str_clean)
                        logger.warning("JSON parsed after aggressive cleaning")
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error: {str(e)}. JSON string (first 500 chars): {json_str[:500]}")
                        raise ValueError(f"LLM tra ve JSON khong hop le: {str(e)}")
            else:
                raise ValueError("LLM khong tra ve JSON hop le")
            
            # Validate result
            if 'sql' not in result:
                raise ValueError("Missing 'sql' field in LLM response")
            
            # Replace placeholders
            sql = result['sql']
            sql = sql.replace(':user_id', str(user_id))
            sql = sql.replace(':max_rows', str(SQL_MAX_ROWS))
            result['sql'] = sql
            
            logger.info(f"Generated SQL: {sql[:200]}...")
            logger.info(f"Chart type: {result.get('chart_type')}, x={result.get('x_column')}, y={result.get('y_column')}")
            
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
            logger.info(f"Executing SQL: {sql[:200]}...")
            # Security: Chi cho phep SELECT
            if not sql.strip().upper().startswith('SELECT'):
                logger.warning(f"Non-SELECT query rejected: {sql[:100]}")
                return {
                    'success': False,
                    'error': "Chi cho phep SELECT queries"
                }
            
            # Execute
            result = await session.execute(text(sql))
            rows = result.fetchall()
            
            # Convert to list of dict
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = []
            
            logger.info(f"SQL executed successfully: {len(data)} rows returned")
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
    
    async def text_to_data(self, question: str, user_id: int = 1) -> Dict[str, Any]:
        """
        End-to-end: question → SQL → data
        
        Args:
            question: User question
            user_id: User ID
        
        Returns:
            Dict voi sql, data, chart_type, explanation
        """
        # Step 1: Generate SQL
        sql_result = await self.generate_sql(question, user_id)
        
        if not sql_result['success']:
            return sql_result
        
        # Step 2: Execute SQL
        async with async_session_maker() as session:
            exec_result = await self.execute_sql(sql_result['sql'], session)
        
        if not exec_result['success']:
            return {
                'success': False,
                'error': exec_result['error'],
                'sql': sql_result['sql']
            }
        
        # Step 3: Combine results
        return {
            'success': True,
            'sql': sql_result['sql'],
            'explanation': sql_result['explanation'],
            'data': exec_result['data'],
            'row_count': exec_result['row_count'],
            'chart_type': sql_result['chart_type'],
            'x_column': sql_result['x_column'],
            'y_column': sql_result['y_column']
        }


# Global instance
_sql_generator = None

async def get_sql_generator() -> SQLGenerator:
    """Get or create global SQL generator instance"""
    global _sql_generator
    
    if _sql_generator is None:
        _sql_generator = SQLGenerator()
    
    return _sql_generator

