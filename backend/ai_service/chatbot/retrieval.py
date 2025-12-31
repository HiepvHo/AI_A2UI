# -*- coding: utf-8 -*-
"""
Enhanced Retrieval Strategy - Emotion Chatbot
Query expansion + multi-query search + deduplication
"""

from typing import List, Dict, Optional
from groq import Groq
from ...config.config import GROQ_API_KEY, LLM_MODEL


class EnhancedRetrieval:
    """Enhanced retrieval voi query expansion va multi-query search"""
    
    def __init__(self):
        """Khoi tao enhanced retrieval"""
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.model = LLM_MODEL
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Expand query thanh nhieu queries lien quan
        
        Args:
            query: Original query
            
        Returns:
            List cac queries mo rong
        """
        try:
            prompt = f"""
            Câu hỏi gốc: "{query}"
            
            Hãy sinh ra 2-3 câu hỏi LIÊN QUAN hoặc từ khóa liên quan để tìm kiếm tốt hơn.
            
            Ví dụ:
            - "Tôi buồn" → ["cảm giác buồn bã", "triệu chứng trầm cảm", "cách vượt qua buồn"]
            - "Căng thẳng công việc" → ["stress công việc", "áp lực làm việc", "burnout"]
            
            CHỈ TRẢ VỀ CÁC TỪ KHÓA, CÁCH NHAU BẰNG DẤU |
            Không giải thích, không số thứ tự.
            
            Trả về:
            """
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            expanded_text = response.choices[0].message.content.strip()
            
            # Parse response
            queries = [q.strip() for q in expanded_text.split('|') if q.strip()]
            
            # Add original query
            all_queries = [query] + queries[:3]  # Max 4 queries total
            
            return all_queries
            
        except Exception as e:
            print(f"Query expansion error: {e}")
            return [query]  # Fallback to original
    
    async def search_with_expansion(
        self, 
        query: str, 
        embedding_manager,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Tim kiem voi query expansion
        
        Args:
            query: Original query
            embedding_manager: Embedding manager instance
            top_k: So luong ket qua mong muon
            
        Returns:
            List documents da deduplicate
        """
        try:
            # Step 1: Expand query
            expanded_queries = await self.expand_query(query)
            print(f"Expanded queries: {expanded_queries}")
            
            # Step 2: Search with each query
            all_chunks = []
            seen_ids = set()
            
            for exp_query in expanded_queries:
                chunks = await embedding_manager.search_similar(exp_query, top_k=top_k * 2)
                
                # Deduplicate by ID
                for chunk in chunks:
                    chunk_id = chunk.get('id')
                    if chunk_id and chunk_id not in seen_ids:
                        all_chunks.append(chunk)
                        seen_ids.add(chunk_id)
            
            # Step 3: Sort by relevance score (cao nhat truoc)
            all_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Step 4: Return top K
            return all_chunks[:top_k]
            
        except Exception as e:
            print(f"Enhanced retrieval error: {e}")
            # Fallback to basic search
            return await embedding_manager.search_similar(query, top_k=top_k)


# Global instance
_enhanced_retrieval = None


async def get_enhanced_retrieval() -> EnhancedRetrieval:
    """Get or create global enhanced retrieval instance"""
    global _enhanced_retrieval
    
    if _enhanced_retrieval is None:
        _enhanced_retrieval = EnhancedRetrieval()
    
    return _enhanced_retrieval

