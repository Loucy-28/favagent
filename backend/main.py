from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from models import engine, Base, SessionLocal, Video, Tag, Reminder, UserPreference, video_tag_association
from schemas import (
    VideoCreate, VideoUpdate, VideoOut,
    TagCreate, TagOut,
    PreferenceOut, PreferenceUpdate,
    ReminderOut, StatsOut, PLATFORMS,
)
from services.ai_agent import agent
from services.reminder import (
    start_scheduler, stop_scheduler,
    get_pending_reminders, mark_reminder_read, mark_all_reminders_read,
    get_smart_suggestion, check_and_create_reminders,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_default_data()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="FavAgent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_default_data():
    with SessionLocal() as db:
        if not db.query(UserPreference).first():
            db.add(UserPreference(reminder_days=settings.DEFAULT_REMINDER_DAYS))
            db.commit()

        default_tags = [
            ("干货", "#6366f1"), ("教程", "#8b5cf6"), ("有趣", "#ec4899"),
            ("推荐", "#f59e0b"), ("待学习", "#10b981"), ("待看", "#06b6d4"),
            ("合集", "#f97316"), ("高能", "#ef4444"), ("治愈", "#84cc16"),
            ("测评", "#3b82f6"),
        ]
        for name, color in default_tags:
            if not db.query(Tag).filter(Tag.name == name).first():
                db.add(Tag(name=name, color=color, is_system=True))
        db.commit()


# ──────────────────── Video Endpoints ────────────────────

@app.get("/api/videos", response_model=list[VideoOut])
def list_videos(
    category: str = None,
    tag: str = None,
    platform: str = None,
    watched: bool = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Video)
    if category:
        query = query.filter(Video.category == category)
    if platform:
        query = query.filter(Video.platform == platform)
    if watched is not None:
        query = query.filter(Video.is_watched == watched)
    if search:
        query = query.filter(Video.title.contains(search))
    if tag:
        query = query.filter(Video.tags.any(Tag.name == tag))

    return query.order_by(Video.favorited_at.desc()).all()


@app.post("/api/videos", response_model=VideoOut)
def add_video(video_data: VideoCreate, db: Session = Depends(get_db)):
    result = agent.classify_video(video_data.title, video_data.description, video_data.platform)

    video = Video(
        title=video_data.title,
        url=video_data.url,
        platform=video_data.platform,
        description=video_data.description,
        cover_url=video_data.cover_url,
        author=video_data.author,
        category=result["category"],
    )
    db.add(video)
    db.flush()

    for tag_name in result["tags"]:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, color="#6366f1")
            db.add(tag)
            db.flush()
        video.tags.append(tag)

    for tag_id in video_data.tag_ids:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if tag and tag not in video.tags:
            video.tags.append(tag)

    db.commit()
    db.refresh(video)
    return video


@app.get("/api/videos/{video_id}", response_model=VideoOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video


@app.put("/api/videos/{video_id}", response_model=VideoOut)
def update_video(video_id: int, data: VideoUpdate, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if data.title is not None:
        video.title = data.title
    if data.category is not None:
        video.category = data.category
    if data.is_watched is not None:
        video.is_watched = data.is_watched
    if data.tag_ids is not None:
        video.tags.clear()
        for tag_id in data.tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                video.tags.append(tag)

    db.commit()
    db.refresh(video)
    return video


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    db.delete(video)
    db.commit()
    return {"message": "删除成功"}


@app.post("/api/videos/{video_id}/watched", response_model=VideoOut)
def mark_watched(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    video.is_watched = True
    reminders = db.query(Reminder).filter(Reminder.video_id == video_id).all()
    for r in reminders:
        r.is_read = True
    db.commit()
    db.refresh(video)
    return video


@app.post("/api/videos/{video_id}/reclassify", response_model=VideoOut)
def reclassify_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    result = agent.classify_video(video.title, video.description, video.platform)
    video.category = result["category"]

    video.tags.clear()
    for tag_name in result["tags"]:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, color="#6366f1")
            db.add(tag)
            db.flush()
        video.tags.append(tag)

    db.commit()
    db.refresh(video)
    return video


# ──────────────────── Tag Endpoints ────────────────────

@app.get("/api/tags", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).order_by(Tag.is_system.desc(), Tag.name).all()


@app.post("/api/tags", response_model=TagOut)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    existing = db.query(Tag).filter(Tag.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    tag = Tag(name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@app.delete("/api/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    if tag.is_system:
        raise HTTPException(status_code=400, detail="系统标签不可删除")
    db.delete(tag)
    db.commit()
    return {"message": "删除成功"}


# ──────────────────── Reminder Endpoints ────────────────────

@app.get("/api/reminders", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return get_pending_reminders(db)


@app.put("/api/reminders/{reminder_id}/read")
def read_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = mark_reminder_read(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return {"message": "已标记为已读"}


@app.put("/api/reminders/read-all")
def read_all_reminders(db: Session = Depends(get_db)):
    mark_all_reminders_read(db)
    return {"message": "全部已读"}


@app.post("/api/reminders/check")
def trigger_reminder_check(db: Session = Depends(get_db)):
    check_and_create_reminders()
    return {"message": "提醒检查完成"}


# ──────────────────── Preference Endpoints ────────────────────

@app.get("/api/preferences", response_model=PreferenceOut)
def get_preferences(db: Session = Depends(get_db)):
    pref = db.query(UserPreference).first()
    if not pref:
        pref = UserPreference()
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@app.put("/api/preferences", response_model=PreferenceOut)
def update_preferences(data: PreferenceUpdate, db: Session = Depends(get_db)):
    pref = db.query(UserPreference).first()
    if not pref:
        pref = UserPreference()
        db.add(pref)
        db.flush()

    if data.reminder_days is not None:
        pref.reminder_days = data.reminder_days
    if data.auto_classify is not None:
        pref.auto_classify = data.auto_classify
    if data.smart_reminder is not None:
        pref.smart_reminder = data.smart_reminder

    db.commit()
    db.refresh(pref)
    return pref


@app.get("/api/preferences/smart-suggestion")
def smart_suggestion(db: Session = Depends(get_db)):
    return get_smart_suggestion(db)


# ──────────────────── Stats & Misc ────────────────────

@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    total = len(videos)
    watched = sum(1 for v in videos if v.is_watched)
    pending = db.query(Reminder).filter(Reminder.is_read == False).count()

    categories = {}
    tag_counts = {}
    for v in videos:
        categories[v.category] = categories.get(v.category, 0) + 1
        for t in v.tags:
            tag_counts[t.name] = tag_counts.get(t.name, 0) + 1

    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    return StatsOut(
        total=total,
        watched=watched,
        unwatched=total - watched,
        pending_reminders=pending,
        top_categories=[{"name": c, "count": n} for c, n in top_categories],
        top_tags=[{"name": t, "count": n} for t, n in top_tags],
    )


@app.get("/api/summary")
def get_summary(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    video_dicts = [
        {"is_watched": v.is_watched, "category": v.category}
        for v in videos
    ]
    return {"summary": agent.generate_summary(video_dicts)}


@app.get("/api/platforms")
def get_platforms():
    return PLATFORMS


@app.get("/api/agent/status")
def agent_status():
    return {
        "ai_enabled": agent.ai_enabled,
        "model": settings.OPENAI_MODEL if agent.ai_enabled else "rule-based-fallback",
        "message": "AI 模型已连接，可进行智能分类" if agent.ai_enabled else "使用规则引擎进行基础分类（配置 OPENAI_API_KEY 可启用 AI 模式）",
    }


# ──────────────────── Static Files ────────────────────

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")
