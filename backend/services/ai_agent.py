import json
import re
from typing import Optional
from openai import OpenAI

from config import settings

CATEGORY_SYSTEM_PROMPT = """你是一个视频分类和标签专家。根据用户收藏的视频信息，你需要：
1. 判断视频属于哪个分类（从下面的分类列表中选择最合适的）
2. 为视频生成3-5个精准的标签
3. 用一句话总结视频内容

可选分类列表：
- 技术编程：编程、开发、算法、系统设计、技术教程等
- 科技数码：手机、电脑、数码产品、科技资讯、产品评测等
- 学习教育：课程、考试、学术、语言学习、知识科普等
- 生活日常：美食、旅行、家居、购物、生活技巧等
- 游戏电竞：游戏实况、游戏攻略、电竞赛事、游戏评测等
- 影视娱乐：电影、电视剧、综艺、动漫、明星八卦等
- 音乐舞蹈：歌曲、MV、乐器、舞蹈、音乐教程等
- 运动健身：健身、球类、跑步、瑜伽、运动教程等
- 财经商业：投资理财、商业分析、经济学、创业、职场等
- 艺术设计：绘画、摄影、设计、手工、创意等
- 资讯新闻：时事新闻、社会热点、行业动态等
- 其他：不属于以上任何分类

请严格按照以下JSON格式返回结果，不要包含其他内容：
{"category": "分类名称", "tags": ["标签1", "标签2", "标签3"], "summary": "一句话总结"}"""

FALLBACK_CATEGORIES = {
    "技术编程": [
        "编程", "代码", "开发", "python", "java", "javascript", "react", "vue",
        "算法", "数据结构", "系统", "架构", "api", "框架", "后端", "前端", "全栈",
        "数据库", "mysql", "linux", "git", "docker", "kubernetes", "ai", "机器学习",
        "深度学习", "程序", "debug", "bug", "部署", "服务器", "web", "app",
    ],
    "科技数码": [
        "手机", "电脑", "数码", "评测", "测评", "iphone", "android", "华为",
        "苹果", "小米", "显卡", "cpu", "gpu", "硬件", "芯片", "5g", "人工智能",
        "机器人", "vr", "ar", "智能", "新品", "发布", "科技",
    ],
    "学习教育": [
        "课程", "学习", "教程", "考试", "高考", "考研", "英语", "数学", "物理",
        "化学", "历史", "地理", "大学", "高中", "初中", "留学", "论文", "学术",
        "知识", "科普", "讲解", "教学", "培训",
    ],
    "生活日常": [
        "美食", "做饭", "食谱", "旅行", "旅游", "vlog", "日常", "家居", "装修",
        "收纳", "清洁", "购物", "好物", "推荐", "生活", "技巧", "妙招", "穿搭",
        "护肤", "化妆", "穿搭",
    ],
    "游戏电竞": [
        "游戏", "攻略", "实况", "电竞", "比赛", "lol", "王者", "原神",
        "吃鸡", "fps", "moba", "rpg", "steam", "主机", "switch", "ps5",
        "xbox", "手游", "网游", "单机",
    ],
    "影视娱乐": [
        "电影", "电视剧", "综艺", "动漫", "动画", "剪辑", "解说", "影评",
        "影视", "剧情", "明星", "八卦", "娱乐", "真人秀", "纪录片",
    ],
    "音乐舞蹈": [
        "音乐", "歌曲", "mv", "演唱会", "乐器", "吉他", "钢琴", "唱歌",
        "翻唱", "原创", "舞蹈", "跳舞", "编舞", "街舞", "古典", "流行",
        "摇滚", "电子", "说唱", "rap",
    ],
    "运动健身": [
        "健身", "减肥", "增肌", "瑜伽", "跑步", "篮球", "足球", "乒乓球",
        "羽毛球", "游泳", "健身操", "拉伸", "运动", "训练", "体能",
    ],
    "财经商业": [
        "投资", "理财", "股票", "基金", "经济", "金融", "商业", "创业",
        "职场", "面试", "工作", "薪资", "公司", "管理", "营销", "品牌",
        "财务", "分析", "行业",
    ],
    "艺术设计": [
        "绘画", "画画", "素描", "水彩", "油画", "摄影", "拍照", "设计",
        "平面设计", "ui", "ux", "手工", "diy", "创意", "插画", "字体",
    ],
    "资讯新闻": [
        "新闻", "热点", "时事", "事件", "发布", "公告", "政策", "法规",
        "动态", "报道", "采访", "评论", "分析",
    ],
}

FALLBACK_TAGS = {
    "技术编程": ["编程", "开发", "技术", "代码", "教程"],
    "科技数码": ["科技", "数码", "评测", "产品", "新品"],
    "学习教育": ["学习", "教育", "知识", "课程", "干货"],
    "生活日常": ["生活", "日常", "分享", "推荐", "实用"],
    "游戏电竞": ["游戏", "电竞", "攻略", "实况", "娱乐"],
    "影视娱乐": ["影视", "娱乐", "推荐", "解说", "精彩"],
    "音乐舞蹈": ["音乐", "好听", "舞蹈", "表演", "才艺"],
    "运动健身": ["运动", "健身", "健康", "训练", "活力"],
    "财经商业": ["财经", "商业", "投资", "职场", "干货"],
    "艺术设计": ["艺术", "设计", "创意", "美学", "灵感"],
    "资讯新闻": ["资讯", "新闻", "热点", "关注", "最新"],
    "其他": ["有趣", "收藏", "待看", "推荐", "精选"],
}


class AIAgent:
    def __init__(self):
        self.client: Optional[OpenAI] = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        self._use_ai = self.client is not None

    @property
    def ai_enabled(self) -> bool:
        return self._use_ai

    def classify_video(self, title: str, description: str = "", platform: str = "") -> dict:
        if self._use_ai:
            return self._classify_with_ai(title, description, platform)
        return self._classify_with_rules(title, description, platform)

    def _classify_with_ai(self, title: str, description: str, platform: str) -> dict:
        user_content = f"视频标题：{title}\n"
        if description:
            user_content += f"视频描述：{description}\n"
        if platform:
            user_content += f"来源平台：{platform}\n"

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": CATEGORY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"[AIAgent] AI classification failed, falling back to rules: {e}")

        return self._classify_with_rules(title, description, platform)

    def _classify_with_rules(self, title: str, description: str, platform: str) -> dict:
        text = f"{title} {description}".lower()
        best_category = "其他"
        best_score = 0

        for category, keywords in FALLBACK_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_category = category

        if best_score == 0:
            best_category = "其他"

        base_tags = FALLBACK_TAGS.get(best_category, ["收藏", "待看"])
        extra_tags = self._extract_extra_tags(title, text)
        tags = list(dict.fromkeys(base_tags[:3] + extra_tags))[:5]

        summary = f"来自{platform}的{best_category}内容" if platform else f"一个{best_category}相关的视频"

        return {
            "category": best_category,
            "tags": tags,
            "summary": summary,
        }

    def _extract_extra_tags(self, title: str, text: str) -> list[str]:
        tag_patterns = {
            "干货": ["干货", "必看", "收藏级"],
            "教程": ["教程", "教学", "入门", "从零开始"],
            "测评": ["测评", "评测", "对比", "实测"],
            "合集": ["合集", "盘点", "汇总", "大全"],
            "搞笑": ["搞笑", "笑死", "哈哈", "沙雕"],
            "治愈": ["治愈", "温暖", "感动", "暖心"],
            "高能": ["高能", "震撼", "惊艳", "太强了"],
        }
        found = []
        for tag, keywords in tag_patterns.items():
            if any(kw in text for kw in keywords):
                found.append(tag)
        return found

    def optimize_reminder_timing(self, user_videos: list[dict]) -> dict:
        if not user_videos:
            return {"suggested_days": 3, "reason": "暂无足够的观看数据，使用默认提醒周期"}

        watched_count = sum(1 for v in user_videos if v.get("is_watched"))
        total_count = len(user_videos)

        if total_count == 0:
            return {"suggested_days": 3, "reason": "暂无收藏数据"}

        watch_rate = watched_count / total_count

        if watch_rate > 0.7:
            return {
                "suggested_days": 5,
                "reason": f"你的观看率很高({watch_rate:.0%})，可以适当延长提醒间隔",
            }
        elif watch_rate < 0.3:
            return {
                "suggested_days": 2,
                "reason": f"你的观看率较低({watch_rate:.0%})，建议缩短提醒间隔帮助消化收藏",
            }
        else:
            return {
                "suggested_days": 3,
                "reason": f"你的观看率良好({watch_rate:.0%})，当前提醒间隔合适",
            }

    def generate_summary(self, videos: list[dict]) -> str:
        if not videos:
            return "收藏夹空空如也，快去收藏一些好内容吧！"

        total = len(videos)
        watched = sum(1 for v in videos if v.get("is_watched"))
        categories = {}
        for v in videos:
            cat = v.get("category", "其他")
            categories[cat] = categories.get(cat, 0) + 1

        top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        cat_str = "、".join(f"{c}({n}个)" for c, n in top_cats)

        return (
            f"你共收藏了 {total} 个视频，"
            f"已观看 {watched} 个，还有 {total - watched} 个待观看。"
            f"主要集中在{cat_str}领域。"
        )


agent = AIAgent()
