# -*- coding: utf-8 -*-
"""
Initialize Database - Emotion Chatbot
Tao tables va seed sample data
Chay: python scripts/init_database.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import date, time, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import init_db, async_session_maker
from backend.database.models import (
    User, EmotionTopic, EmotionLog, MoodEntry, CrisisAlert
)
from backend.config.config import EMOTION_TOPICS


async def seed_emotion_topics():
    """Seed 11 emotion topics"""
    print("  Seeding emotion topics...")
    
    async with async_session_maker() as session:
        for topic_data in EMOTION_TOPICS:
            topic = EmotionTopic(
                id=topic_data["id"],
                name=topic_data["name"],
                name_vi=topic_data["name_vi"],
                icon=topic_data["icon"],
                color=topic_data["color"],
                is_active=True
            )
            session.add(topic)
        
        await session.commit()
    
    print(f"  -> Seeded {len(EMOTION_TOPICS)} topics")


async def seed_sample_user():
    """Tao sample user voi emotion logs"""
    print("  Creating sample user...")
    
    async with async_session_maker() as session:
        # Tao user
        user = User(
            name="Test User",
            age=25
        )
        session.add(user)
        await session.flush()
        
        # Tao emotion logs cho 30 ngay
        today = date.today()
        emotion_labels_pool = [
            ["buon", "lo"],
            ["vui", "hanh phuc"],
            ["gian", "buc"],
            ["lo au", "stress"],
            ["binh thuong"],
            ["met moi"],
            ["tu tin"],
            ["nang dong"]
        ]
        
        for day_offset in range(30):
            log_date = today - timedelta(days=day_offset)
            
            # Random 1-2 logs moi ngay
            num_logs = random.randint(1, 2)
            for _ in range(num_logs):
                topic_id = random.choice([1, 2, 5, 6, 11])  # Random topics
                intensity = random.randint(2, 4)
                labels = random.choice(emotion_labels_pool)
                
                log = EmotionLog(
                    user_id=user.id,
                    date=log_date,
                    time=time(random.randint(8, 22), random.randint(0, 59)),
                    topic_id=topic_id if random.random() > 0.2 else None,  # 20% khong chon topic
                    emotion_labels=labels,
                    intensity=intensity,
                    note=f"Cam xuc ngay {log_date}",
                    triggers=["cong viec", "gia dinh"] if random.random() > 0.5 else []
                )
                session.add(log)
        
        # Tao mood entries cho 30 ngay
        for day_offset in range(30):
            entry_date = today - timedelta(days=day_offset)
            
            mood = MoodEntry(
                user_id=user.id,
                date=entry_date,
                mood_score=random.randint(4, 8),
                energy_level=random.randint(4, 8),
                sleep_quality=random.randint(5, 9),
                journal_text=f"Nhat ky ngay {entry_date}",
                grateful_for="Gia dinh, ban be"
            )
            session.add(mood)
        
        await session.commit()
        print(f"  -> Created user with 30 days emotion logs")


async def main():
    """Main function"""
    print("=" * 60)
    print("KHOI TAO DATABASE - EMOTION CHATBOT")
    print("=" * 60)
    
    print("\n1. Creating tables...")
    await init_db()
    print("  -> Tables created")
    
    print("\n2. Seeding data...")
    await seed_emotion_topics()
    await seed_sample_user()
    
    print("\n" + "=" * 60)
    print("HOAN THANH!")
    print("Database san sang cho emotion chatbot")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

