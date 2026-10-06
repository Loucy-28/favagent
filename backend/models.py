from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime, timezone

from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


video_tag_association = Table(
    "video_tags", Base.metadata,
    Column("video_id", Integer, ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), default="")
    platform = Column(String(100), default="other")
    description = Column(Text, default="")
    cover_url = Column(String(1000), default="")
    author = Column(String(200), default="")
    category = Column(String(100), default="未分类")
    is_watched = Column(Boolean, default=False)
    favorited_at = Column(DateTime, default=utcnow)
    reminded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    tags = relationship("Tag", secondary=video_tag_association, back_populates="videos")
    reminders = relationship("Reminder", back_populates="video", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#6366f1")
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    videos = relationship("Video", secondary=video_tag_association, back_populates="tags")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    video = relationship("Video", back_populates="reminders")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    reminder_days = Column(Integer, default=3)
    auto_classify = Column(Boolean, default=True)
    smart_reminder = Column(Boolean, default=True)
