# -*- coding: utf-8 -*-
"""
A2UI Generator - Emotion Chatbot
Tao A2UI JSON blocks tu LLM output
6 block types: text, card, list, chart, button, divider
"""

from typing import Dict, Any, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class A2UIGenerator:
    """Generate A2UI JSON blocks cho frontend rendering"""
    
    def __init__(self):
        pass
    
    def create_text_block(self, content: str, style: str = "normal") -> Dict[str, Any]:
        """
        Text block
        
        Args:
            content: Noi dung text
            style: normal|heading|subheading|caption
        """
        return {
            'type': 'text',
            'id': self._generate_id(),
            'content': content,
            'style': style
        }
    
    def create_card_block(
        self, 
        title: str, 
        description: str, 
        color: str = "#3B82F6",
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Card block (highlight box)
        
        Args:
            title: Tieu de
            description: Mo ta
            color: Hex color
            icon: Emoji icon
        """
        return {
            'type': 'card',
            'id': self._generate_id(),
            'title': title,
            'description': description,
            'color': color,
            'icon': icon
        }
    
    def create_list_block(
        self, 
        items: List[str], 
        list_type: str = "bullet",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List block
        
        Args:
            items: Danh sach items
            list_type: bullet|numbered|checkbox
            title: Tieu de list (optional)
        """
        return {
            'type': 'list',
            'id': self._generate_id(),
            'title': title,
            'list_type': list_type,
            'items': items
        }
    
    def create_chart_block(
        self, 
        chart_spec: Dict[str, Any], 
        chart_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chart block (Plotly)
        
        Args:
            chart_spec: Plotly JSON spec
            chart_id: Unique ID de map insights
            title: Tieu de chart
        """
        return {
            'type': 'chart',
            'id': self._generate_id(),
            'chart_id': chart_id,
            'title': title,
            'spec': chart_spec
        }
    
    def create_button_block(
        self, 
        label: str, 
        action: str,
        style: str = "primary"
    ) -> Dict[str, Any]:
        """
        Button block
        
        Args:
            label: Text tren button
            action: Action identifier (e.g., "ask_question", "view_history")
            style: primary|secondary|danger
        """
        return {
            'type': 'button',
            'id': self._generate_id(),
            'label': label,
            'action': action,
            'style': style
        }
    
    def create_divider_block(self) -> Dict[str, Any]:
        """Divider block (horizontal line)"""
        return {
            'type': 'divider',
            'id': self._generate_id()
        }
    
    def create_blocks_from_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Tao danh sach A2UI blocks tu RAG response
        
        Args:
            response_data: Dict voi keys: answer, chart_spec, chart_id, suggestions, etc.
        
        Returns:
            List of A2UI blocks
        """
        blocks = []
        
        # 1. Main answer text (split neu qua dai)
        if 'answer' in response_data and response_data['answer']:
            answer_text = response_data['answer'].strip()
            
            # Split answer thanh paragraphs neu co
            paragraphs = answer_text.split('\n\n')
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Detect heading (neu bat dau bang so hoac **)
                if para.startswith(('1.', '2.', '3.', '4.', '5.', '**', '##', '###')):
                    # Extract heading va content
                    lines = para.split('\n', 1)
                    if len(lines) > 1:
                        heading = lines[0].strip().replace('**', '').replace('#', '').strip()
                        content = lines[1].strip()
                        blocks.append(self.create_text_block(heading, style='subheading'))
                        if content:
                            blocks.append(self.create_text_block(content, style='normal'))
                    else:
                        blocks.append(self.create_text_block(para, style='normal'))
                else:
                    blocks.append(self.create_text_block(para, style='normal'))
        
        # 2. Chart (neu co)
        chart_spec = response_data.get('chart_spec')
        if chart_spec and isinstance(chart_spec, dict):
            # Validate chart_spec has required fields
            if chart_spec.get('data') and chart_spec.get('layout'):
                chart_id = response_data.get('chart_id') or f"chart_{self._generate_id()}"
                chart_title = response_data.get('chart_title') or 'Biểu đồ'
                blocks.append(self.create_chart_block(
                    chart_spec=chart_spec,
                    chart_id=chart_id,
                    title=chart_title
                ))
                logger.info(f"[A2UI] Added chart block: chart_id={chart_id}")
            else:
                logger.warning(f"[A2UI] Invalid chart_spec: missing data or layout. Spec keys: {chart_spec.keys() if chart_spec else 'None'}")
        
        # 3. Insights card (neu co)
        if 'insights' in response_data and response_data['insights']:
            blocks.append(self.create_card_block(
                title="Nhan xet",
                description=response_data['insights'],
                color="#10B981",
                icon=None
            ))
        
        # 4. Suggestions text (neu co) - hien thi nhu 1 cau tu nhien
        if 'suggestions' in response_data and response_data['suggestions']:
            # Suggestions la 1 string, khong phai list
            suggestion_text = response_data['suggestions']
            if isinstance(suggestion_text, str) and suggestion_text.strip():
                blocks.append(self.create_text_block(
                    content=suggestion_text,
                    style='normal'
                ))
        
        # 5. Divider (chi them neu co it nhat 1 block khac)
        if len(blocks) > 0:
            blocks.append(self.create_divider_block())
        
        logger.info(f"Generated {len(blocks)} A2UI blocks: types={[b.get('type') for b in blocks]}")
        return blocks
    
    def _generate_id(self) -> str:
        """Generate unique ID cho block"""
        return str(uuid.uuid4())[:8]


# Global instance
_a2ui_generator = None

def get_a2ui_generator() -> A2UIGenerator:
    """Get or create global A2UI generator instance"""
    global _a2ui_generator
    
    if _a2ui_generator is None:
        _a2ui_generator = A2UIGenerator()
    
    return _a2ui_generator

