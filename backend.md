# ZenithTask - 后端开发文档 (FastAPI 与 SQLite)

**版本：** 1.3  
**日期：** 2025年6月6日  
**项目代号：** ZenithTask

> **重要提示：** 此版本文档将数据库从 Supabase (PostgreSQL) 迁移到 SQLite，旨在简化开发和部署流程，尤其适用于中小型应用或原型开发。SQLite 是一个轻量级的、基于文件的数据库，与 PostgreSQL 在并发性、可伸缩性和某些高级功能上有所不同。

## 1. 技术选型 (后端部分修订)

### 1.1. 后端
- **语言/框架：**
  - Python
  - FastAPI：现代、高性能的 Web 框架，基于 Python 3.7+ 类型提示，自动生成交互式 API 文档（Swagger UI, ReDoc），异步支持优秀。
- **API 规范：** RESTful（FastAPI 自动生成 OpenAPI 规范）
- **数据库交互：**
  - SQLAlchemy（推荐）：功能强大的 Python SQL 工具包和对象关系映射器，可与 FastAPI 配合使用，连接到 SQLite 数据库。
- **数据库：**
  - SQLite：一个C语言库，实现了一个小型、快速、自包含、高可靠性、功能齐全的SQL数据库引擎。数据库将是一个本地文件（例如 `zenithtask.db`）。

### 1.2. 文件存储
- 本地文件系统或第三方对象存储：对于用户头像等文件，可以考虑存储在服务器的本地文件系统（需要注意备份和扩展性），或集成第三方对象存储服务（如 AWS S3, MinIO 等）。SQLite 本身不直接处理文件存储。

### 1.3. 其他工具与服务（后端相关）
- **版本控制：** Git（GitHub, GitLab, Bitbucket）
- **身份认证：**
  - FastAPI 内置/社区方案（推荐）：例如，使用 FastAPI 的 `OAuth2PasswordBearer` 结合 passlib 进行密码哈希，并将用户信息存储在 SQLite 数据库中。也可以考虑 `fastapi-users` 等库，它支持多种数据库后端，包括 SQLAlchemy（可用于 SQLite）。
- **部署：**
  - FastAPI 应用：Docker + Uvicorn/Hypercorn。可部署到各类云平台（如 AWS, Google Cloud, Azure）或 VPS。SQLite 数据库文件需要与应用一起部署，并确保持久化存储（例如使用 Docker 卷）。

## 2. 数据模型与表结构 (SQLite)

以下是核心数据表的详细设计。SQLite 的数据类型与 PostgreSQL 有所不同。通常使用 `INTEGER PRIMARY KEY AUTOINCREMENT` 作为主键。

### 2.1. 用户 (users)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 用户唯一标识
email TEXT UNIQUE NOT NULL -- 用户邮箱
hashed_password TEXT NOT NULL -- 哈希后的用户密码
full_name TEXT -- 用户全名
avatar_url TEXT -- 用户头像 URL (指向文件存储位置)
preferences TEXT -- 用户偏好设置 (JSON 字符串，如 {"theme": "dark", "default_view": "kanban"})
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 用户创建时间
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 用户信息最后更新时间
is_active BOOLEAN DEFAULT true -- 用户是否激活
is_superuser BOOLEAN DEFAULT false -- 是否为超级用户
```

### 2.2. 项目 (projects)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 项目唯一标识
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE -- 所属用户
name TEXT NOT NULL -- 项目名称
description TEXT -- 项目描述
color_hex TEXT -- 项目代表色 (如 "#FF5733")
view_preference TEXT -- 项目默认视图 (如 'kanban', 'list', 'calendar')
is_archived BOOLEAN DEFAULT false -- 是否已归档
archived_at DATETIME -- 归档时间
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 创建时间
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 最后更新时间
```

### 2.3. 任务 (tasks)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 任务唯一标识
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE -- 所属用户
project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL -- 所属项目（可为空）
parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE -- 父任务ID
title TEXT NOT NULL -- 任务标题
description TEXT -- 任务详细描述
status TEXT NOT NULL DEFAULT 'todo' -- 任务状态（如 'todo', 'inprogress', 'done', 'archived'）
priority INTEGER DEFAULT 0 -- 优先级（0:无, 1:低, 2:中, 3:高）
due_date DATETIME -- 截止日期和时间
scheduled_start_time DATETIME -- 计划开始时间
scheduled_end_time DATETIME -- 计划结束时间
actual_start_time DATETIME -- 实际开始时间
completed_at DATETIME -- 任务完成时间
estimated_duration_minutes INTEGER -- 预计花费时长（分钟）
actual_duration_minutes INTEGER -- 实际花费时长（分钟）
order_in_list REAL -- 用于排序
is_recurring BOOLEAN DEFAULT false -- 是否为重复任务
recurring_schedule TEXT -- 重复规则（JSON 字符串，如 {"type": "daily"}）
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 创建时间
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 最后更新时间
```

### 2.4. 标签 (tags)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 标签唯一标识
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE -- 所属用户
name TEXT NOT NULL -- 标签名称
color_hex TEXT -- 标签颜色（如 "#33FF57"）
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 创建时间
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 最后更新时间
CONSTRAINT uq_user_tag_name UNIQUE (user_id, name) -- 同一用户下的标签名唯一
```

### 2.5. 任务标签关联表 (task_tags)
```sql
task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE
tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE
assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 分配标签的时间
PRIMARY KEY (task_id, tag_id)
```

### 2.6. 专注时段 (focus_sessions)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 专注时段唯一标识
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE -- 所属用户
task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL -- 关联的任务
start_time DATETIME NOT NULL -- 专注开始时间
end_time DATETIME NOT NULL -- 专注结束时间
duration_minutes INTEGER NOT NULL -- 专注时长（分钟）
notes TEXT -- 专注时段备注
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 记录创建时间
```

### 2.7. 精力记录 (energy_logs)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT -- 精力记录唯一标识
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE -- 所属用户
timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP -- 精力记录时间点
energy_level INTEGER NOT NULL CHECK (energy_level >= 1 AND energy_level <= 5) -- 精力水平
source TEXT -- 记录来源（如 'user_input', 'system_prompt'）
notes TEXT -- 精力备注
created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 记录创建时间
```

## 数据库索引建议
- `projects.user_id`

tasks.user_id
tasks.project_id
tasks.parent_task_id
tasks.status
tasks.due_date
tags.user_id
focus_sessions.user_id
focus_sessions.task_id
energy_logs.user_id
energy_logs.timestamp
注意: SQLite 对于 updated_at 字段的自动更新，通常依赖于应用层面 (例如 SQLAlchemy 的事件监听器) 或在支持的版本中使用 UPDATE ... SET updated_at = CURRENT_TIMESTAMP。SQLite 的触发器语法与 PostgreSQL 不同。
