from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class Platform(str, Enum):
    bilibili = "bilibili"
    douyin = "douyin"
    xiaohongshu = "xiaohongshu"
    zhihu = "zhihu"
    youtube = "youtube"
    weixin = "weixin"
    other = "other"


class PlatformInfo(BaseModel):
    value: str
    label: str
    icon: str


PLATFORMS: list[PlatformInfo] = [
    PlatformInfo(value="bilibili", label="哔哩哔哩", icon="📺"),
    PlatformInfo(value="douyin", label="抖音", icon="🎵"),
    PlatformInfo(value="xiaohongshu", label="小红书", icon="📕"),
    PlatformInfo(value="zhihu", label="知乎", icon="💡"),
    PlatformInfo(value="youtube", label="YouTube", icon="▶️"),
    PlatformInfo(value="weixin", label="微信视频号", icon="💬"),
    PlatformInfo(value="other", label="其他", icon="🔗"),
]


class TagBase(BaseModel):
    name: str
    color: str = "#6366f1"


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    id: int
    is_system: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    title: str
    url: str = ""
    platform: str = "other"
    description: str = ""
    cover_url: str = ""
    author: str = ""


class VideoCreate(VideoBase):
    tag_ids: list[int] = []


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    is_watched: Optional[bool] = None
    tag_ids: Optional[list[int]] = None


class VideoOut(VideoBase):
    id: int
    category: str = "未分类"
    is_watched: bool = False
    favorited_at: Optional[datetime] = None
    reminded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    tags: list[TagOut] = []

    class Config:
        from_attributes = True


class PreferenceOut(BaseModel):
    id: int = 1
    reminder_days: int = 3
    auto_classify: bool = True
    smart_reminder: bool = True

    class Config:
        from_attributes = True


class PreferenceUpdate(BaseModel):
    reminder_days: Optional[int] = None
    auto_classify: Optional[bool] = None
    smart_reminder: Optional[bool] = None


class ReminderOut(BaseModel):
    id: int
    video_id: int
    video: Optional[VideoOut] = None
    remind_at: Optional[datetime] = None
    is_read: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClassifyResult(BaseModel):
    category: str
    tags: list[str]
    summary: str = ""


class StatsOut(BaseModel):
    total: int = 0
    watched: int = 0
    unwatched: int = 0
    pending_reminders: int = 0
    top_categories: list[dict] = []
    top_tags: list[dict] = []
