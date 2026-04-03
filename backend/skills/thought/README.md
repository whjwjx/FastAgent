# 🧠 ThoughtSkill (想法与笔记管理技能)

## 📖 技能介绍
ThoughtSkill 是 FastXpoAgent 的核心内置技能之一，专为帮助用户记录和管理日常碎片化灵感、笔记、博客长文或周报而设计。通过该技能，Agent 可以直接将信息沉淀到后端的数据库中，并借助 Embedding 技术（如需）为将来的语义检索做准备。

## 🎯 核心能力
- **记录想法 (`thought:crud:create`)**: 能够记录短文本灵感，也能存储 AI 整理好的长篇 Markdown 报告或博客。支持添加多标签 (`tags`)，以及关联来源 (`source_ids`)。
- **查询想法 (`thought:crud:read`)**: 支持获取用户最近的想法，或者通过关键字模糊搜索历史记录。
- **更新想法 (`thought:crud:update`)**: 修改特定 ID 的想法内容，并同步重新计算该内容的语义向量 (Embedding)。
- **删除想法 (`thought:crud:delete`)**: 批量或单条逻辑删除用户的想法，保证数据隔离和安全。

## ⚙️ 设计规范
- **Python Schema**: 接口参数严格遵守 OpenAI Function Calling 规范定义（详见 `schema.py`）。
- **原生操作**: 内部 CRUD 逻辑均基于 SQLAlchemy 的 `Session` 同步完成，充分复用连接池。
- **软删除**: 删除操作为 `is_deleted = True` 的软删除，防止误删带来的数据丢失。
