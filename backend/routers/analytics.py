"""
Analytics Router - API endpoints for interactive charts and explanations
"""

from datetime import date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from groq import Groq

from ..database.connection import get_db
from ..database.models import EmotionLog, EmotionTopic
from ..config.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyticsSummaryResponse(BaseModel):
    success: bool = Field(True, description="Success status")
    data: List[Dict[str, Any]] = Field(
        default_factory=list, description="Emotion records for charting"
    )
    row_count: int = Field(0, description="Number of rows returned")
    chart_type: str = Field("line", description="Suggested chart type")
    x_column: str = Field("date", description="X axis column")
    y_column: str = Field("intensity", description="Y axis column")
    explanation: Optional[str] = Field(
        None, description="Short description of the dataset"
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    user_id: int = Query(..., description="User ID"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    emotion: Optional[str] = Query(None, description="Filter by emotion label"),
    trigger: Optional[str] = Query(None, description="Filter by trigger"),
    topic_id: Optional[int] = Query(None, description="Filter by topic_id"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trả về dữ liệu cảm xúc thô để hiển thị chart (không dùng LLM).
    Hỗ trợ lọc theo ngày, emotion label, trigger, topic.
    """
    try:
        stmt = (
            select(
                EmotionLog.date,
                EmotionLog.intensity,
                EmotionLog.emotion_labels,
                EmotionLog.triggers,
                EmotionLog.note,
                EmotionTopic.name_vi.label("topic_name"),
            )
            .join(EmotionTopic, EmotionLog.topic_id == EmotionTopic.id, isouter=True)
            .where(EmotionLog.user_id == user_id)
            .order_by(EmotionLog.date.asc())
        )

        if date_from:
            stmt = stmt.where(EmotionLog.date >= date_from)
        if date_to:
            stmt = stmt.where(EmotionLog.date <= date_to)
        if emotion:
            stmt = stmt.where(EmotionLog.emotion_labels.any(emotion))
        if trigger:
            stmt = stmt.where(EmotionLog.triggers.any(trigger))
        if topic_id:
            stmt = stmt.where(EmotionLog.topic_id == topic_id)

        result = await db.execute(stmt)
        rows = result.fetchall()

        data: List[Dict[str, Any]] = []
        for row in rows:
            data.append(
                {
                    "date": row.date.isoformat() if row.date else None,
                    "intensity": row.intensity,
                    "emotion_labels": row.emotion_labels or [],
                    "triggers": row.triggers or [],
                    "topic_name": row.topic_name,
                    "note": row.note,
                }
            )

        # Xay dung explanation dong dua tren filters va ket qua
        filters: List[str] = []
        if date_from and date_to:
            filters.append(f"từ {date_from.isoformat()} đến {date_to.isoformat()}")
        elif date_from:
            filters.append(f"từ {date_from.isoformat()}")
        elif date_to:
            filters.append(f"đến {date_to.isoformat()}")

        if emotion:
            filters.append(f"cảm xúc chứa nhãn \"{emotion}\"")
        if trigger:
            filters.append(f"kích hoạt liên quan đến \"{trigger}\"")
        if topic_id:
            filters.append(f"thuộc chủ đề cảm xúc ID {topic_id}")

        if filters:
            filter_text = "; ".join(filters)
        else:
            filter_text = "toàn bộ dữ liệu cảm xúc đã ghi nhận"

        if len(data) == 0:
            explanation = (
                f"Không tìm thấy bản ghi cảm xúc nào cho bộ lọc: {filter_text}."
            )
        else:
            explanation = (
                f"Tìm thấy {len(data)} bản ghi cảm xúc cho bộ lọc: {filter_text}. "
                "Biểu đồ dùng trục thời gian (x = date) và mức độ cảm xúc (y = intensity)."
            )

        return AnalyticsSummaryResponse(
            success=True,
            data=data,
            row_count=len(data),
            chart_type="line",
            x_column="date",
            y_column="intensity",
            explanation=explanation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics summary: {str(e)}")


class EmotionOptionsResponse(BaseModel):
    success: bool = Field(True)
    emotions: List[str] = Field(default_factory=list)


@router.get("/emotions", response_model=EmotionOptionsResponse)
async def list_emotions(
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trả về danh sách emotion_labels (distinct) cho dropdown filter.
    """
    try:
        stmt = select(func.distinct(func.unnest(EmotionLog.emotion_labels))).where(
            EmotionLog.user_id == user_id
        )
        result = await db.execute(stmt)
        rows = result.fetchall()
        emotions = [r[0] for r in rows if r[0]]
        return EmotionOptionsResponse(success=True, emotions=emotions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotions: {str(e)}")


class ExplainRequest(BaseModel):
    """Request model for chart explanation"""
    user_id: int = Field(..., description="User ID")
    date_from: Optional[date] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[date] = Field(None, description="End date (YYYY-MM-DD)")
    point_date: Optional[date] = Field(None, description="Specific date to explain (YYYY-MM-DD)")
    emotion: Optional[str] = Field(None, description="Filter by emotion label")
    trigger: Optional[str] = Field(None, description="Filter by trigger")
    topic_id: Optional[int] = Field(None, description="Filter by topic_id")


class ExplainResponse(BaseModel):
    """Response model for chart explanation"""
    success: bool = Field(True, description="Success status")
    explanation: str = Field(..., description="LLM-generated explanation")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="Data statistics")


@router.post("/explain", response_model=ExplainResponse)
async def explain_chart_selection(
    request: ExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Giải thích một phần chart được user chọn (gọi LLM on-demand).
    User click vào điểm hoặc chọn range trên chart → gọi API này để LLM phân tích.
    """
    try:
        # Xay dung query voi filters
        stmt = (
            select(
                EmotionLog.date,
                EmotionLog.intensity,
                EmotionLog.emotion_labels,
                EmotionLog.triggers,
                EmotionLog.note,
                EmotionTopic.name_vi.label("topic_name"),
            )
            .join(EmotionTopic, EmotionLog.topic_id == EmotionTopic.id, isouter=True)
            .where(EmotionLog.user_id == request.user_id)
        )

        # Ap dung filters
        if request.point_date:
            # Nếu có point_date, chỉ lấy data của ngày đó
            stmt = stmt.where(EmotionLog.date == request.point_date)
        else:
            # Nếu không có point_date, dùng date range
            if request.date_from:
                stmt = stmt.where(EmotionLog.date >= request.date_from)
            if request.date_to:
                stmt = stmt.where(EmotionLog.date <= request.date_to)

        if request.emotion:
            stmt = stmt.where(EmotionLog.emotion_labels.any(request.emotion))
        if request.trigger:
            stmt = stmt.where(EmotionLog.triggers.any(request.trigger))
        if request.topic_id:
            stmt = stmt.where(EmotionLog.topic_id == request.topic_id)

        stmt = stmt.order_by(EmotionLog.date.asc()).limit(50)  # Limit để tránh quá nhiều data

        result = await db.execute(stmt)
        rows = result.fetchall()

        if len(rows) == 0:
            return ExplainResponse(
                success=True,
                explanation="Không có dữ liệu để phân tích trong khoảng thời gian đã chọn.",
                data_summary={"row_count": 0}
            )

        # Format data cho LLM
        data_records = []
        emotions_count = {}
        triggers_count = {}
        intensity_sum = 0
        intensity_count = 0

        for row in rows:
            record = {
                "date": row.date.isoformat() if row.date else None,
                "intensity": row.intensity,
                "emotion_labels": row.emotion_labels or [],
                "triggers": row.triggers or [],
                "topic_name": row.topic_name,
                "note": row.note,
            }
            data_records.append(record)

            # Dem thong ke
            if row.emotion_labels:
                for em in row.emotion_labels:
                    emotions_count[em] = emotions_count.get(em, 0) + 1
            if row.triggers:
                for tr in row.triggers:
                    triggers_count[tr] = triggers_count.get(tr, 0) + 1
            if row.intensity:
                intensity_sum += row.intensity
                intensity_count += 1

        avg_intensity = intensity_sum / intensity_count if intensity_count > 0 else 0
        top_emotions = sorted(emotions_count.items(), key=lambda x: x[1], reverse=True)[:3]
        top_triggers = sorted(triggers_count.items(), key=lambda x: x[1], reverse=True)[:2]

        # Xay dung data summary
        data_summary = {
            "row_count": len(rows),
            "avg_intensity": round(avg_intensity, 2),
            "top_emotions": [{"emotion": em, "count": count} for em, count in top_emotions],
            "top_triggers": [{"trigger": tr, "count": count} for tr, count in top_triggers],
        }

        # Format data sample cho LLM (lay 10 records dau)
        data_sample_text = ""
        for i, record in enumerate(data_records[:10], 1):
            data_sample_text += f"\n{i}. Ngày {record['date']}: "
            if record['emotion_labels']:
                data_sample_text += f"Cảm xúc: {', '.join(record['emotion_labels'])}, "
            if record['triggers']:
                data_sample_text += f"Lý do: {', '.join(record['triggers'])}, "
            data_sample_text += f"Intensity: {record['intensity']}/5"
            if record['topic_name']:
                data_sample_text += f", Chủ đề: {record['topic_name']}"

        # Xay dung context description
        context_desc = ""
        if request.point_date:
            context_desc = f"Ngày {request.point_date.isoformat()}"
        elif request.date_from and request.date_to:
            context_desc = f"Từ {request.date_from.isoformat()} đến {request.date_to.isoformat()}"
        elif request.date_from:
            context_desc = f"Từ {request.date_from.isoformat()}"
        elif request.date_to:
            context_desc = f"Đến {request.date_to.isoformat()}"

        if request.emotion:
            context_desc += f", cảm xúc: {request.emotion}"
        if request.trigger:
            context_desc += f", trigger: {request.trigger}"
        if request.topic_id:
            context_desc += f", topic ID: {request.topic_id}"

        # Generate explanation voi LLM
        groq_client = Groq(api_key=GROQ_API_KEY)
        
        prompt = f"""Bạn là một người bạn thân thiết, ấm áp. Hãy giải thích về cảm xúc của người dùng một cách tự nhiên, gần gũi bằng tiếng Việt.

Khoảng thời gian: {context_desc}
Thông tin cảm xúc:
- Cảm xúc thường gặp: {', '.join([em for em, _ in top_emotions]) if top_emotions else 'Không có'}
- Lý do thường gặp: {', '.join([tr for tr, _ in top_triggers]) if top_triggers else 'Không có'}
- Cảm xúc: {'rất mạnh' if avg_intensity >= 4 else 'mạnh' if avg_intensity >= 3 else 'nhẹ' if avg_intensity >= 2 else 'rất nhẹ'}

Một số ngày cụ thể:
{data_sample_text}

Yêu cầu:
- Viết 2-3 câu ngắn gọn, ấm áp như một người bạn đang tâm sự
- Dùng từ gần gũi: "Mình thấy bạn...", "Có vẻ như bạn...", "Chắc bạn đã..."
- Tránh nói về số liệu, thống kê - tập trung vào cảm xúc
- Đưa ra lời động viên nhẹ nhàng: "Cố gắng lên nhé", "Bạn có thể thử...", "Mình tin bạn sẽ..."
- KHÔNG dùng: "mức độ cường độ", "tỷ lệ", "thống kê", "dữ liệu cho thấy"
- Thay vào đó: "bạn có nhiều ngày cảm thấy...", "cảm xúc chủ yếu là...", "mình thấy bạn thường..."

Ví dụ:
"Mình thấy trong khoảng thời gian này bạn có nhiều ngày cảm thấy buồn và lo lắng, chủ yếu liên quan đến công việc. Chắc bạn đã trải qua những ngày khá căng thẳng. Cố gắng lên nhé, bạn có thể thử các cách thư giãn như thở sâu hoặc chia sẻ với người thân để giảm bớt áp lực."

Giải thích:"""

        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=LLM_TEMPERATURE,
            max_tokens=200
        )

        explanation = response.choices[0].message.content.strip()

        return ExplainResponse(
            success=True,
            explanation=explanation,
            data_summary=data_summary
        )

    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

