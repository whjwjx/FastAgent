# FastAIStack

FastAIStack 是一个基于 **AI Agent 架构** 和 **前后端极致分离理念** 构建的多用户、轻量级 AI 助手平台。

本项目致力于提供一种在 AI 原生时代下的工程范式：**前端仅作为“展示层与交互层”，而所有的“思考”（意图识别、复杂任务拆解）与“行动”（数据CRUD、第三方API调用）全部下沉至后端大模型（Agent 中枢）承载。**

---

## 🏗 技术架构

### 核心设计理念
1. **Agent 中枢路由模式**：摒弃传统的关键词或正则表达式做意图识别，引入 LLM 作为系统的“大脑（Router）”。
2. **多端支持与模块化单体**：前端使用 Expo 构建，一套代码同时适配 Web、iOS 和 Android；内部采用模块化解耦，可按需挂载或卸载独立功能模块（如“想法”、“日程”）。
3. **数据隔离与安全**：基于 PostgreSQL 实现多租户（多用户）数据安全隔离，配合 Refresh Token 提供无感刷新防数据丢失的极佳体验。

### 技术栈
| 模块 | 技术选型 | 核心职责 |
| --- | --- | --- |
| **Frontend (前端)** | [Expo](https://expo.dev/) (React Native) | **零业务逻辑**。纯粹负责跨端 UI 渲染、状态管理（如 Token 缓存防丢）、接口调用。 |
| **Backend (后端)** | [FastAPI](https://fastapi.tiangolo.com/) (Python) | **全业务逻辑**。提供 RESTful API，承载 Token 鉴权、Agent 中枢调度、各业务模块的 CRUD。 |
| **Database (数据库)** | PostgreSQL | 持久化存储用户、日程、想法等数据，从底层通过 `user_id` 保障多用户数据隔离。 |
| **AI Layer (大模型)** | 兼容主流 LLM API (如通义、文心等) | 担任系统意图拆解与内容生成的引擎。 |

---

## 📂 目录结构

```text
FastAIStack/
├── backend/                # 后端代码目录
│   └── main.py             # FastAPI 应用入口点
├── frontend/               # 前端代码目录
│   ├── app/                # Expo 页面路由组件
│   ├── components/         # 共享 UI 组件
│   └── package.json        # 前端依赖配置
└── docs/                   # 项目设计与文档目录
    └── PRD.md              # 核心产品需求文档与架构蓝图
```

---

## 🚀 快速启动

### 1. 启动后端 (FastAPI)
后端采用 FastAPI 构建，确保你已经安装了 Python 环境。
```bash
cd backend
# 建议使用虚拟环境：python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
```
后端服务启动后，可以访问 `http://localhost:8000/docs` 查看自动生成的 API 接口文档。

### 2. 启动前端 (Expo)
前端采用 Expo (React Native) 框架，确保你已经安装了 Node.js 环境。
```bash
cd frontend
npm install
npx expo start
```
- 按 `w` 在 Web 浏览器中打开
- 按 `a` 在 Android 模拟器中打开
- 按 `i` 在 iOS 模拟器中打开

---

## 🎯 业务链路示例（日程与想法记录）

1. **用户输入**：“我明天要去北京出差，顺便写个总结”
2. **前端**：将文本与用户的 Token 直接抛给后端。
3. **后端（Agent Router）**：大模型识别出这是一个“混合意图”，将其拆解为两步：
   - 调度 **日程 Agent**，提取出“明天，去北京出差”，并调用后端对应的日历 CRUD 接口存入数据库。
   - 调度 **想法 Agent**，提取出“写个出差总结”，并存入该用户的想法记录表中。
4. **前端**：接收到后端的处理完成状态，自动刷新并渲染对应的日历与想法列表。

---

## 🛡️ 许可与规范

请参考项目规范进行开发，并优先阅读 `docs/PRD.md` 了解本项目的详细产品设计与边界约束。
