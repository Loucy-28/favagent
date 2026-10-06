"""
初始化数据库并导入示例数据，方便快速体验项目功能。
运行方式：python scripts/init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta, timezone
from models import engine, Base, SessionLocal, Video, Tag, UserPreference
from services.ai_agent import agent

SAMPLE_VIDEOS = [
    {"title": "Python 异步编程完全指南：从 asyncio 到 FastAPI 实战", "platform": "bilibili", "author": "技术派", "description": "深入讲解 Python 异步编程的核心概念和实际应用"},
    {"title": "2024 最值得买的机械键盘推荐", "platform": "xiaohongshu", "author": "数码小王", "description": "十款高性价比机械键盘横评"},
    {"title": "深度学习论文精读：Attention Is All You Need", "platform": "bilibili", "author": "AI研究员", "description": "Transformer 架构的详细解读"},
    {"title": "三分钟学会做正宗四川麻婆豆腐", "platform": "douyin", "author": "厨房达人", "description": "地道川味麻婆豆腐的家庭做法"},
    {"title": "React 19 新特性全面解析", "platform": "bilibili", "author": "前端食堂", "description": "React 19 Server Components 和 Actions 深度讲解"},
    {"title": "考研数学一 高数核心考点总结", "platform": "zhihu", "author": "考研帮", "description": "高等数学重难点和解题技巧汇总"},
    {"title": "原神 4.8 版本全角色强度排行", "platform": "bilibili", "author": "原神攻略组", "description": "最新深渊环境下的角色推荐"},
    {"title": "日本东京 Vlog：秋叶原和涩谷的一天", "platform": "xiaohongshu", "author": "旅行少女", "description": "东京热门打卡地点分享"},
    {"title": "Docker + K8s 微服务部署实战", "platform": "bilibili", "author": "运维老司机", "description": "从零搭建完整的微服务部署流水线"},
    {"title": "2024 年度最佳电影盘点", "platform": "douyin", "author": "影评人老李", "description": "今年不可错过的十部好电影"},
    {"title": "吉他入门教程：零基础学弹唱", "platform": "youtube", "author": "MusicTeacher", "description": "适合初学者的吉他教学系列"},
    {"title": "居家健身计划：每天15分钟练出好身材", "platform": "douyin", "author": "健身教练Amy", "description": "不需要器械的居家训练方案"},
    {"title": "A股投资入门：新手必知的五个原则", "platform": "zhihu", "author": "理财顾问", "description": "稳健投资的基础知识分享"},
    {"title": "UI 设计趋势 2024：玻璃拟态与新拟物", "platform": "xiaohongshu", "author": "设计师小林", "description": "最新 UI 设计风格分析和案例"},
    {"title": "GPT-5 会带来什么变化？AI 行业深度分析", "platform": "bilibili", "author": "科技观察", "description": "大语言模型发展趋势预测"},
]

PLATFORM_COLORS = {
    "bilibili": "#00a1d6",
    "douyin": "#161823",
    "xiaohongshu": "#ff2442",
    "zhihu": "#0066ff",
    "youtube": "#ff0000",
    "weixin": "#07c160",
    "other": "#6b7280",
}


def init():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.query(Video).count() > 0:
            print("数据库已有数据，跳过初始化。如需重新初始化请先删除 favagent.db 文件。")
            return

        if not db.query(UserPreference).first():
            db.add(UserPreference(reminder_days=3, auto_classify=True, smart_reminder=True))

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

        now = datetime.now(timezone.utc)
        for i, data in enumerate(SAMPLE_VIDEOS):
            result = agent.classify_video(data["title"], data.get("description", ""), data["platform"])

            days_ago = i * 1.5
            fav_time = now - timedelta(days=days_ago)

            video = Video(
                title=data["title"],
                url=f"https://example.com/video/{i+1}",
                platform=data["platform"],
                description=data.get("description", ""),
                author=data.get("author", ""),
                category=result["category"],
                is_watched=i % 3 == 0,
                favorited_at=fav_time,
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

        db.commit()
        print(f"✅ 初始化完成！已导入 {len(SAMPLE_VIDEOS)} 个示例视频。")
        print("🚀 运行 'uvicorn backend.main:app --reload' 启动服务。")


if __name__ == "__main__":
    init()
