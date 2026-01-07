# -*- coding: utf-8 -*-
"""
Chart Generator - Emotion Chatbot
Tao Plotly chart spec tu SQL data
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import date, datetime, time

from ...config.config import CHART_DEFAULT_HEIGHT, CHART_DEFAULT_COLORS

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate Plotly chart specifications from data"""
    
    def __init__(self):
        self.default_height = CHART_DEFAULT_HEIGHT
        self.default_colors = CHART_DEFAULT_COLORS
    
    def generate_chart(
        self, 
        data: List[Dict[str, Any]], 
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        title: str = "Chart"
    ) -> Dict[str, Any]:
        """
        Generate Plotly chart specification
        
        Args:
            data: List of dicts (SQL query results)
            chart_type: bar|line|pie|scatter|table
            x_column: Column name cho truc x
            y_column: Column name cho truc y
            title: Chart title
        
        Returns:
            Plotly chart spec (JSON)
        """
        logger.debug(f"Generating chart: type={chart_type}, rows={len(data)}")
        
        if not data:
            logger.warning("No data for chart")
            return self._empty_chart(title)
        
        # Auto-detect columns neu chua co
        if not x_column or not y_column:
            x_column, y_column = self._auto_detect_columns(data, chart_type)
            logger.debug(f"Auto-detected: x={x_column}, y={y_column}")
        
        # Serialize data (xu ly date/time)
        data = self._serialize_data(data)
        
        # Generate chart theo type
        try:
            if chart_type == 'bar':
                chart_spec = self._bar_chart(data, x_column, y_column, title)
            elif chart_type == 'line':
                chart_spec = self._line_chart(data, x_column, y_column, title)
            elif chart_type == 'pie':
                chart_spec = self._pie_chart(data, x_column, y_column, title)
            elif chart_type == 'scatter':
                chart_spec = self._scatter_chart(data, x_column, y_column, title)
            elif chart_type == 'table':
                chart_spec = self._table_chart(data, title)
            else:
                logger.warning(f"Unknown chart_type, using bar")
                chart_spec = self._bar_chart(data, x_column, y_column, title)
            
            logger.debug(f"Chart generated: {chart_type}")
            return chart_spec
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            return self._empty_chart(title)
    
    def _serialize_data(self, data: List[Dict]) -> List[Dict]:
        """Convert date/time/datetime to string de JSON serialize"""
        serialized = []
        for row in data:
            new_row = {}
            for key, value in row.items():
                if isinstance(value, (date, datetime)):
                    new_row[key] = value.isoformat()
                elif isinstance(value, time):
                    new_row[key] = value.isoformat()
                else:
                    new_row[key] = value
            serialized.append(new_row)
        return serialized
    
    def _auto_detect_columns(self, data: List[Dict], chart_type: str) -> tuple:
        """Tu dong detect x va y columns"""
        if not data:
            return ('x', 'y')
        
        columns = list(data[0].keys())
        
        if len(columns) < 2:
            return (columns[0], columns[0])
        
        # Heuristic: column dau = x, column sau = y (numeric)
        x_col = columns[0]
        y_col = columns[1] if len(columns) > 1 else columns[0]
        
        return (x_col, y_col)
    
    def _empty_chart(self, title: str) -> Dict[str, Any]:
        """Empty chart khi khong co data"""
        return {
            'data': [],
            'layout': {
                'title': title,
                'annotations': [{
                    'text': 'Khong co du lieu',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 20}
                }]
            }
        }
    
    def _bar_chart(self, data: List[Dict], x_col: str, y_col: str, title: str) -> Dict[str, Any]:
        """Bar chart"""
        x_values = [row.get(x_col, '') for row in data]
        y_values = [row.get(y_col, 0) for row in data]
        
        return {
            'data': [{
                'type': 'bar',
                'x': x_values,
                'y': y_values,
                'marker': {'color': self.default_colors[0]},
                'hovertemplate': f'<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>'
            }],
            'layout': {
                'title': {'text': title, 'font': {'size': 18}},
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'height': self.default_height,
                'hovermode': 'closest'
            }
        }
    
    def _line_chart(self, data: List[Dict], x_col: str, y_col: str, title: str) -> Dict[str, Any]:
        """Line chart"""
        x_values = [row.get(x_col, '') for row in data]
        y_values = [row.get(y_col, 0) for row in data]
        
        return {
            'data': [{
                'type': 'scatter',
                'mode': 'lines+markers',
                'x': x_values,
                'y': y_values,
                'line': {'color': self.default_colors[1], 'width': 2},
                'marker': {'size': 6},
                'hovertemplate': f'<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>'
            }],
            'layout': {
                'title': {'text': title, 'font': {'size': 18}},
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'height': self.default_height,
                'hovermode': 'closest'
            }
        }
    
    def _pie_chart(self, data: List[Dict], label_col: str, value_col: str, title: str) -> Dict[str, Any]:
        """Pie chart"""
        labels = [row.get(label_col, '') for row in data]
        values = [row.get(value_col, 0) for row in data]
        
        return {
            'data': [{
                'type': 'pie',
                'labels': labels,
                'values': values,
                'marker': {'colors': self.default_colors},
                'hovertemplate': '<b>%{label}</b><br>%{value} (%{percent})<extra></extra>'
            }],
            'layout': {
                'title': {'text': title, 'font': {'size': 18}},
                'height': self.default_height
            }
        }
    
    def _scatter_chart(self, data: List[Dict], x_col: str, y_col: str, title: str) -> Dict[str, Any]:
        """Scatter chart"""
        x_values = [row.get(x_col, 0) for row in data]
        y_values = [row.get(y_col, 0) for row in data]
        
        return {
            'data': [{
                'type': 'scatter',
                'mode': 'markers',
                'x': x_values,
                'y': y_values,
                'marker': {'size': 10, 'color': self.default_colors[3]},
                'hovertemplate': f'<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>'
            }],
            'layout': {
                'title': {'text': title, 'font': {'size': 18}},
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'height': self.default_height,
                'hovermode': 'closest'
            }
        }
    
    def _table_chart(self, data: List[Dict], title: str) -> Dict[str, Any]:
        """Table chart (Plotly table)"""
        if not data:
            return self._empty_chart(title)
        
        columns = list(data[0].keys())
        
        # Prepare header va cells
        header_values = columns
        cell_values = [[row.get(col, '') for row in data] for col in columns]
        
        return {
            'data': [{
                'type': 'table',
                'header': {
                    'values': header_values,
                    'align': 'left',
                    'font': {'size': 12, 'color': 'white'},
                    'fill': {'color': self.default_colors[0]}
                },
                'cells': {
                    'values': cell_values,
                    'align': 'left',
                    'font': {'size': 11},
                    'fill': {'color': ['#f5f5f5', 'white']}
                }
            }],
            'layout': {
                'title': {'text': title, 'font': {'size': 18}},
                'height': self.default_height
            }
        }


# Global instance
_chart_generator = None

def get_chart_generator() -> ChartGenerator:
    """Get or create global chart generator instance"""
    global _chart_generator
    
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    
    return _chart_generator

