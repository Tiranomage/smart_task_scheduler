from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from datetime import datetime

# Database URL - using SQLite for simplicity
SQLALCHEMY_DATABASE_URL = "sqlite:///./smart_task_scheduler.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)  # 1-5 scale
    urgent = Column(Boolean, default=False)  # Based on deadline proximity
    important = Column(Boolean, default=False)  # User-defined importance
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    estimated_duration = Column(Integer, default=30)  # in minutes
    actual_duration = Column(Integer, nullable=True)  # in minutes, when completed
    scheduled_start = Column(DateTime, nullable=True)  # When it's scheduled to start
    scheduled_end = Column(DateTime, nullable=True)  # When it's scheduled to end
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, default="manual")  # manual, google_calendar, todoist

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)