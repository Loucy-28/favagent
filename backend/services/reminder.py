from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from models import SessionLocal, Video, Reminder, UserPreference
from services.ai_agent import agent

scheduler = BackgroundScheduler()


def check_and_create_reminders():
    with SessionLocal() as db:
        pref = db.query(UserPreference).first()
        if not pref:
            pref = UserPreference(reminder_days=3)
            db.add(pref)
            db.commit()
            db.refresh(pref)

        reminder_days = pref.reminder_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=reminder_days)

        unwatched = (
            db.query(Video)
            .filter(Video.is_watched == False)
            .filter(Video.favorited_at <= cutoff)
            .all()
        )

        for video in unwatched:
            existing = (
                db.query(Reminder)
                .filter(Reminder.video_id == video.id)
                .filter(Reminder.is_read == False)
                .first()
            )
            if not existing:
                reminder = Reminder(
                    video_id=video.id,
                    remind_at=datetime.now(timezone.utc),
                )
                db.add(reminder)
                video.reminded_at = datetime.now(timezone.utc)

        db.commit()


def get_pending_reminders(db, skip: int = 0, limit: int = 20):
    return (
        db.query(Reminder)
        .filter(Reminder.is_read == False)
        .order_by(Reminder.remind_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def mark_reminder_read(db, reminder_id: int):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder:
        reminder.is_read = True
        db.commit()
    return reminder


def mark_all_reminders_read(db):
    db.query(Reminder).filter(Reminder.is_read == False).update({"is_read": True})
    db.commit()


def get_smart_suggestion(db) -> dict:
    videos = db.query(Video).all()
    video_dicts = [
        {"is_watched": v.is_watched, "category": v.category, "favorited_at": str(v.favorited_at)}
        for v in videos
    ]
    return agent.optimize_reminder_timing(video_dicts)


def start_scheduler():
    scheduler.add_job(check_and_create_reminders, "interval", hours=6, id="reminder_check")
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
