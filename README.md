# FavAgent - AI 收藏夹管理助手

> 让你的 AI Agent 帮你管理"吃灰"的收藏夹，智能分类、自动标签、定期提醒，再也不让好内容被遗忘。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Vue](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![License](https://img.shields.io/badge/License-MIT-green)

## 项目背景

我们在小红书、抖音、B站等平台收藏了大量视频，但往往看过一次就再也没打开过。时间一长，收藏夹变成了"吃灰箱"，想找某个视频却翻不到。

**FavAgent** 是一个基于 AI 的收藏夹管理助手，它能在你收藏视频时自动识别内容、智能分类打标签，并定期提醒你回去观看，让收藏真正有价值。

## 核心功能

### 1. AI 智能分类与标签

- 收藏视频时，AI Agent 自动分析视频标题、描述等信息
- 智能归类到 11 大分类（技术编程、科技数码、学习教育、生活日常等）
- 自动生成 3-5 个精准标签
- 支持用户自定义标签和手动调整
- 支持 OpenAI API 智能模式 + 规则引擎兜底模式

### 2. 定期观看提醒

- 默认 3 天未观看自动提醒（可自定义 1-14 天）
- 后台定时任务自动检查并生成提醒
- **AI 自适应优化**：根据用户观看习惯智能调整提醒周期
- 应用内通知 + 一键跳转观看

### 3. 双视图管理

- **按时间分类**：按收藏时间倒序排列，支持按分类和平台筛选
- **按标签分类**：按标签聚合展示，快速找到同类内容
- 全文搜索、平台筛选、分类筛选

## 技术架构

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│          Vue 3 + Tailwind CSS               │
│    (SPA, 响应式设计, 现代化 UI)               │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────┴──────────────────────────┐
│                  Backend                     │
│               FastAPI (Python)               │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ AI Agent │  │ Reminder │  │   Video   │  │
│  │ Service  │  │ Scheduler│  │   CRUD    │  │
│  └──────────┘  └──────────┘  └───────────┘  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│               SQLite Database                │
│     (Videos, Tags, Reminders, Preferences)   │
└─────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 高性能异步 Web 框架 |
| 数据库 | SQLite + SQLAlchemy | 轻量级 ORM 数据持久化 |
| AI 引擎 | OpenAI API | GPT-4o-mini 智能分类（支持切换模型） |
| 定时任务 | APScheduler | 后台定期检查和生成提醒 |
| 前端框架 | Vue 3 (CDN) | 响应式 SPA 界面 |
| 样式 | Tailwind CSS | 原子化 CSS 快速构建现代 UI |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/favagent.git
cd favagent
```

### 2. 创建虚拟环境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量（可选）

```bash
cp ../.env.example ../.env
# 编辑 .env 文件，填入你的 OpenAI API Key
```

> 不配置 API Key 也能运行！项目内置规则引擎作为兜底方案。

### 5. 初始化示例数据

```bash
cd ..
python scripts/init_db.py
```

### 6. 启动服务

```bash
cd backend
uvicorn main:app --reload --port 8000
```

打开浏览器访问 **http://localhost:8000** 即可体验。

## API 接口文档

启动服务后访问 **http://localhost:8000/docs** 查看完整的 Swagger API 文档。

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/videos` | 获取视频列表（支持筛选） |
| POST | `/api/videos` | 收藏新视频（AI 自动分类） |
| PUT | `/api/videos/{id}` | 更新视频信息 |
| DELETE | `/api/videos/{id}` | 删除视频 |
| POST | `/api/videos/{id}/watched` | 标记为已观看 |
| POST | `/api/videos/{id}/reclassify` | AI 重新分类 |
| GET | `/api/tags` | 获取标签列表 |
| POST | `/api/tags` | 创建自定义标签 |
| GET | `/api/reminders` | 获取待观看提醒 |
| GET/PUT | `/api/preferences` | 获取/更新用户设置 |
| GET | `/api/preferences/smart-suggestion` | 获取 AI 提醒优化建议 |
| GET | `/api/stats` | 获取收藏统计 |
| GET | `/api/agent/status` | 查看 AI Agent 状态 |

## 项目亮点

1. **AI Agent 设计**：完整的 Agent 架构，支持 OpenAI 智能模式和规则引擎兜底模式
2. **自适应提醒**：根据用户观看行为数据，AI 动态优化提醒周期
3. **现代全栈**：FastAPI 异步后端 + Vue 3 响应式前端，代码清晰、架构规范
4. **开箱即用**：SQLite 零配置、内置示例数据、无需外部服务即可运行
5. **可扩展性**：模块化设计，易于添加新功能（邮件提醒、多用户支持等）

## 后续扩展方向

- 邮件/微信推送提醒
- 浏览器插件一键收藏
- 多用户支持与数据同步
- 接入更多 AI 模型（本地模型、国产大模型）
- 收藏夹内容周报/月报自动生成
- 视频内容摘要提取

## License

MIT License
