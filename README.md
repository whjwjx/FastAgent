# 🚀 FastAgent

<p align="center">
  <img src="public/multi_task_agent.png" alt="FastAgent - Multi-Task Agent" width="600"/>
</p>

FastAgent 是一个基于 **AI Agent 架构** 和 **前后端极致分离理念** 构建的多用户、轻量级 AI 助手平台。

<p align="center">
  <img src="public/main_view_chatbot.png" alt="FastAgent Chatbot" width="300"/>
</p>

<p align="center">
  <a href="#-核心设计理念">核心设计理念</a> •
  <a href="#-技术栈">技术栈</a> •
  <a href="#-已完成功能">已完成功能</a> •
  <a href="#-快速启动">快速启动</a> •
  <a href="#-后续规划">后续规划</a>
</p>

---

## 🌟 核心设计理念

本项目致力于探索 AI 原生时代下的工程新范式：
- **前端仅作为“展示层与交互层”**，无核心业务逻辑。
- **所有的“思考”与“行动”全部下沉至后端大模型（Agent 中枢）承载。**

### 系统架构图

```mermaid
graph TD 
    %% 样式定义 
    classDef frontend fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px; 
    classDef backend fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px; 
    classDef external fill:#e8f5e9,stroke:#43a047,stroke-width:2px; 

    %% 前端模块 
    subgraph Frontend [前端 Expo 或 React Native - 展示与交互层]
        Client["UI 客户端 (状态管理 & SSE)"] 
    end 
    class Frontend frontend; 

    %% 后端模块 
    subgraph Backend [后端 FastAPI - 核心业务与 Agent 中枢]
        API["API 路由层"] 
        Agent["AI Agent 核心引擎"] 
        Services["业务逻辑与数据库交互"] 
        
        API <--> Agent 
        Agent <--> Services 
    end 
    class Backend backend; 

    %% 外部依赖 
    subgraph External [外部服务与存储]
        LLM["大语言模型 (LLM)"] 
        DB[(PostgreSQL 数据库)] 
    end 
    class External external; 

    %% 调用关系 
    Client <-->|SSE 流式连接| API 
    Agent <-->|Prompt & Tool Calls| LLM 
    Services <--> DB 
```

### 核心特性

1. **🧠 Agent 中枢路由模式**：摒弃传统的关键词或正则表达式做意图识别，引入 LLM 作为系统的“大脑（Router）”。
2. **🧩 多端支持与模块化单体**：前端使用 Expo 构建，一套代码同时适配 Web、iOS 和 Android；内部采用模块化解耦，可按需挂载或卸载独立功能模块（如“想法”、“日程”）。
3. **🛡️ 数据隔离与安全**：基于 PostgreSQL 实现多租户（多用户）数据安全隔离，配合 Token 机制提供无感刷新防数据丢失的极佳体验。

## 🛠️ 技术栈

| 模块 | 技术选型 | 核心职责 |
| --- | --- | --- |
| **Frontend (前端)** | [Expo](https://expo.dev/) (React Native) + Zustand | **零业务逻辑**。纯粹负责跨端 UI 渲染、状态管理、接口调用。 |
| **Backend (后端)** | [FastAPI](https://fastapi.tiangolo.com/) (Python) | **全业务逻辑**。提供 RESTful API，承载 Token 鉴权、Agent 中枢调度、各业务模块的 CRUD。 |
| **Database (数据库)** | PostgreSQL + SQLAlchemy + Alembic | 持久化存储用户、日程、想法等数据，从底层通过 `user_id` 保障多用户数据绝对隔离。 |
| **AI Layer (大模型)** | 兼容主流 LLM API (如通义、文心、OpenAI 等) | 担任系统意图拆解与内容生成的引擎，支持 Function Calling 工具调用。 |

## ✨ 已完成功能 (MVP)

- [x] **🔐 完善的用户系统**：支持用户注册、登录、退出，JWT 鉴权及 Token 失效的自动处理（401 全局拦截与状态管理）。
- [x] **🤖 智能 Agent 中枢**：
  - 支持多轮自然对话，拥有“高情商、博学”的通用人设。
  - **原生 ReAct 循环**：纯原生 Python 实现的大模型调度机制，摒弃繁重的第三方框架（如 LangChain），保持极致轻量。
  - **工具路由分发**：精准识别用户意图，按职责调度独立拆分的工具层模块，保持代码高内聚低耦合。
- [x] **💡 想法管理 (Thoughts)**：通过自然语言即可快速记录、查询、管理个人想法与灵感。
- [x] **🌿 数字花园 (Garden)**：支持想法的公开分享。提供**私密 Token**（临时分享）与**个性化 Slug**（个人主页/简历）双轨链接，并实现后端隐私物理隔离。
- [x] **📅 日程管理 (Schedules)**：一句话即可创建、管理日程计划，自动解析时间与星期。
- [x] **🌐 联网搜索能力**：集成 Tavily API，当模型需要实时信息或突破知识库限制时，自动触发联网搜索。

## 🚀 快速启动

### 1. 启动后端 (FastAPI)
后端采用 FastAPI 构建，确保你已经安装了 Python 环境及 PostgreSQL 数据库。
```bash
cd backend
# 建议使用虚拟环境：python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量 (请复制 .env.example 并修改配置)
cp .env.example .env

# 执行数据库迁移
alembic upgrade head

# 启动服务
uvicorn main:app --host 0.0.0.0 --reload --port 8000
```
后端服务启动后，可以访问 `http://localhost:8000/docs` 查看自动生成的 API 接口文档。

### 2. 启动前端 (Expo)
前端采用 Expo (React Native) 框架，确保你已经安装了 Node.js 环境。
```bash
cd frontend
npm install

# 配置环境变量
cp .env.example .env

# 启动服务
npx expo start
```
- 按 `w` 在 Web 浏览器中打开
- 按 `a` 在 Android 模拟器中打开
- 按 `i` 在 iOS 模拟器中打开

## 🗺️ 后续规划 (Roadmap)

本项目将持续迭代，长期发展方向包括但不限于：

- [ ] **🧠 多 Agent 多任务协同**：引入多 Agent 协作机制，支持复杂任务拆解与并发执行。
- [ ] **📝 智能博客与知识库管理**：支持自然语言让 AI 将对话/讨论内容自动整理为博客文章并发布，增加独立的用户博客展示页面，打造并维护个人专属数字知识库。
- [ ] **�🧩 更多 Agent 工具插件**：如天气查询、邮件管理、文件解析（PDF/Excel）等，让 AI 助手包揽所有数字化的日常任务。
- [ ] **🎨 复杂 UI 的跨端渲染优化**：对于复杂的数据图表或特殊展示页，计划采用 WebView 嵌入纯 Web H5 页面，提升多端一致性与开发效率。
- [ ] **🔄 容错与高可用**：为联网搜索及外部 API 调用增加重试机制和降级策略，保障 AI 助手的稳定性。
- [ ] **🐳 容器化部署优化**：完善 Docker 及 `docker-compose.yml` 配置，实现服务的一键编排与生产环境部署。
- [ ] **💬 多会话与历史记录持久化**：支持创建多个独立的对话记录页，并将所有聊天历史安全持久化至数据库，实现跨设备无缝回溯。
- [ ] **⚡ 灵活的交互控制**：提升用户交互的灵活性，支持在流式输出时随时打断 AI 回复，并优化用户连续提问时的等待处理与排队机制。

## 🤝 欢迎与联系

欢迎大家使用 FastAgent！🎉 让我们一起打造更全能、更智能的个人助手，把所有数字化的繁琐任务都交给 AI 打理！

如果你觉得这个项目对你有帮助，或者对 AI Agent 与前后端分离架构感兴趣，**请给我点个 Star ⭐️ 或者 Fork 关注我的后续更新！** 等我更新更多有趣的功能。

非常欢迎大家一起讨论、提交 Issue 或 Pull Request 参与共建！

📫 **联系我**: [whj_cj2020@163.com](mailto:whj_cj2020@163.com)

## 📄 许可与规范

本项目遵循 [MIT License](LICENSE)（假设）。请参考项目规范进行开发。
