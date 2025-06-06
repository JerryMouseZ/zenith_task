# ZenithTask - 后端 API 端点补全 (FastAPI 与 SQLite) v1.3

本文档基于 "Zenith Task开发文档" (总体规划) 和 "ZenithTask - 后端开发文档 (FastAPI 与 SQLite) v1.3" (具体实现)，补全和细化了后端需要实现的 API 端点。

## 通用约定
- 所有 API 路径以 `/api` 开头。
- 认证：除非特别说明，所有端点都需要用户认证（通过 JWT）。
- 响应体：通常返回 JSON 格式。
  - 成功操作返回相应的数据模型（参考 `schemas.py`）。
  - 创建操作返回 `201 Created`。
  - 删除操作成功返回 `204 No Content`。
  - 错误将返回相应的 HTTP 状态码和错误信息。
- `user_id`：通常从认证的 JWT 中获取，用于数据隔离和授权。

## 1. 用户认证与管理 API (`/api/auth` 和 `/api/users`)

### 1.1. 认证 (`/api/auth`)

#### #### POST `/register`

- 描述：用户注册。
- Request Body：
```json
schemas.UserCreate // 包含 email, password, full_name, avatar_url, preferences
```
- Response Body：
```json
schemas.User // 不含 hashed_password
```
- 逻辑：创建新用户，哈希密码，存入 users 表。

#### POST `/token`
- 描述：用户登录获取 JWT。
- Request Body：
```json
fastapi.security.OAuth2PasswordRequestForm // 包含 username (即 email) 和 password
```
- Response Body：
```json
schemas.Token // 包含 access_token, token_type
```

#### POST `/logout`（可选，依赖于 JWT 处理方式）
- 描述：用户登出。如果 JWT 存储在客户端且有服务端黑名单机制，则需要此接口。如果仅依赖客户端删除 token，则此后端接口可选。
- Response：`200 OK` 或 `204 No Content`

### 1.2. 用户资料与偏好 (`/api/users/me`)

#### GET `/me`
- 描述：获取当前登录用户的详细信息。
- Response Body：
```json
schemas.User
```

#### PUT `/me`
- 描述：更新当前登录用户的个人资料（例如 full_name, avatar_url）。
- Request Body：
```json
schemas.UserUpdate // 允许部分更新
```
- Response Body：
```json
schemas.User
```

#### PUT `/me/password`
- 描述：修改当前登录用户的密码。
- Request Body：
```json
schemas.PasswordUpdate // 包含 current_password, new_password
```
- Response：`204 No Content`

#### GET `/me/preferences`
- 描述：获取当前用户的偏好设置。
- Response Body：
```json
Dict[str, Any] // 对应 users.preferences 字段，解析 JSON 字符串后返回
```

#### PUT `/me/preferences`
- 描述：更新当前用户的偏好设置。
- Request Body：
```json
{"theme": "dark", "default_view": "kanban", "ai_prompt_history": []}
```
- Response Body：
```json
Dict[str, Any] // 更新后的偏好设置
```

## 2. 项目管理 API (`/api/projects`)

#### POST `/`
- 描述：创建新项目。
- Request Body：
```json
schemas.ProjectCreate // 包含 name, description, color_hex, view_preference
```
- Response Body：
```json
schemas.Project // status_code=201
```

#### GET `/`
- 描述：获取当前用户的所有项目。
- Query Params：
  - archived: Optional[bool] = False （筛选是否已归档）
  - skip: int = 0, limit: int = 100 （分页）
- Response Body：
```json
List[schemas.Project]
```

#### GET `/{project_id}`
- 描述：获取特定项目的详情。
- Path Param：
  - project_id: int
- Response Body：
```json
schemas.Project
```
- 权限：校验项目是否属于当前用户。

#### PUT `/{project_id}`
- 描述：更新特定项目。
- Path Param：
  - project_id: int
- Request Body：
```json
schemas.ProjectUpdate // 允许部分更新
```
- Response Body：
```json
schemas.Project
```
- 权限：校验项目是否属于当前用户。

#### DELETE `/{project_id}`
- 描述：删除特定项目（及其关联的任务，根据 ON DELETE CASCADE）。
- Path Param：
  - project_id: int
- Response：`204 No Content`
- 权限：校验项目是否属于当前用户。

## 3. 任务管理 API (`/api/tasks`)

#### POST `/`
- 描述：创建新任务。
- Request Body：
```json
schemas.TaskCreate // 包含 title, project_id (可选), parent_task_id (可选), 等任务属性
```
- Response Body：
```json
schemas.Task // status_code=201
```

#### GET `/`
- 描述：获取当前用户的所有任务，支持多种过滤条件。
- Query Params：
  - project_id: Optional[int] = None
  - parent_task_id: Optional[int] = None
  - status: Optional[str] = None
  - priority: Optional[int] = None
  - due_date_start: Optional[datetime] = None
  - due_date_end: Optional[datetime] = None
  - is_recurring: Optional[bool] = None
  - tags: Optional[List[int]] = None （通过标签 ID 列表筛选，可能需要 JOIN 查询）
  - skip: int = 0, limit: int = 100 （分页）
- Response Body：
```json
List[schemas.Task]
```

#### GET `/{task_id}`
- 描述：获取特定任务的详情。
- Path Param：
  - task_id: int
- Response Body：
```json
schemas.Task // 可考虑是否内嵌子任务 sub_tasks: List[schemas.Task] 和标签 tags: List[schemas.Tag]
```
- 权限：校验任务是否属于当前用户。

#### PUT `/{task_id}`
- 描述：更新特定任务。
- Path Param：
  - task_id: int
- Request Body：
```json
schemas.TaskUpdate // 允许部分更新
```
- Response Body：
```json
schemas.Task
```
- 权限：校验任务是否属于当前用户。

#### DELETE `/{task_id}`
- 描述：删除特定任务。
- Path Param：
  - task_id: int
- Response：`204 No Content`
- 权限：校验任务是否属于当前用户。


#### POST `/{task_id}/subtasks`
- 描述：为特定任务创建子任务。
- Path Param：
  - task_id: int（作为父任务 ID）
- Request Body：
```json
schemas.TaskCreate // 其中 parent_task_id 将被忽略或由服务端设置
```
- Response Body：
```json
schemas.Task // 新创建的子任务
```
- 权限：校验父任务是否属于当前用户。

#### PUT `/reorder`
- 描述：批量更新任务的顺序和/或状态（例如看板拖拽后）。
- Request Body：
```json
List[schemas.TaskReorderItem] // TaskReorderItem 包含 task_id: int, new_order_in_list: Optional[float], new_status: Optional[str], new_project_id: Optional[int]
```
- Response Body：
```json
List[schemas.Task] // 更新后的任务列表
```
- 权限：校验所有被操作的任务是否属于当前用户。

## 4. 标签管理 API (`/api/tags`)

#### POST `/`
- 描述：创建新标签。
- Request Body：
```json
schemas.TagCreate // 包含 name, color_hex
```
- Response Body：
```json
schemas.Tag // status_code=201
```
- 约束：(user_id, name) 需唯一。

#### GET `/`
- 描述：获取当前用户的所有标签。
- Response Body：
```json
List[schemas.Tag]
```

#### GET `/{tag_id}`
- 描述：获取特定标签的详情。
- Path Param：
  - tag_id: int
- Response Body：
```json
schemas.Tag
```
- 权限：校验标签是否属于当前用户。

#### PUT `/{tag_id}`
- 描述：更新特定标签。
- Path Param：
  - tag_id: int
- Request Body：
```json
schemas.TagUpdate // 允许部分更新
```
- Response Body：
```json
schemas.Tag
```
- 权限：校验标签是否属于当前用户。

#### DELETE `/{tag_id}`
- 描述：删除特定标签（同时会从 task_tags 表中移除关联）。
- Path Param：
  - tag_id: int
- Response：`204 No Content`
- 权限：校验标签是否属于当前用户。

### 4.1. 任务与标签关联 API (`/api/tasks/{task_id}/tags`)

#### POST `/{tag_id}`
- 描述：为特定任务添加标签。
- Path Params：
  - task_id: int
  - tag_id: int
- Response Body：
```json
schemas.TaskTag // 或仅 201 Created
```
- 逻辑：在 task_tags 表中创建关联。
- 权限：校验任务和标签是否都属于当前用户。

#### DELETE `/{tag_id}`
- 描述：从特定任务移除标签。
- Path Params：
  - task_id: int
  - tag_id: int
- Response：`204 No Content`
- 逻辑：从 task_tags 表中删除关联。
- 权限：校验任务和标签是否都属于当前用户。

#### GET `/`（在 `/api/tasks/{task_id}/tags` 路径下）
- 描述：获取特定任务的所有标签。
- Path Param：
  - task_id: int
- Response Body：
```json
List[schemas.Tag]
```
- 权限：校验任务是否属于当前用户。

## 5. 监控数据 API (`/api/monitoring`)

### 5.1. 专注时段 (`/focus-sessions`)

#### POST `/`
- 描述：创建新的专注时段记录。
- Request Body：
```json
schemas.FocusSessionCreate // 包含 task_id (可选), start_time, end_time, duration_minutes, notes
```
- Response Body：
```json
schemas.FocusSession // status_code=201
```

#### GET `/`
- 描述：获取当前用户的专注时段记录。
- Query Params：
  - task_id: Optional[int] = None
  - date_start: Optional[datetime] = None
  - date_end: Optional[datetime] = None
  - skip: int = 0, limit: int = 100 （分页）
- Response Body：
```json
List[schemas.FocusSession]
```

#### GET `/{session_id}`
- 描述：获取特定专注时段的详情。
- Path Param：
  - session_id: int
- Response Body：
```json
schemas.FocusSession
```
- 权限：校验记录是否属于当前用户。

#### PUT `/{session_id}`
- 描述：更新特定专注时段（例如修改备注）。
- Path Param：
  - session_id: int
- Request Body：
```json
schemas.FocusSessionUpdate
```
- Response Body：
```json
schemas.FocusSession
```
- 权限：校验记录是否属于当前用户。

#### DELETE `/{session_id}`
- 描述：删除特定专注时段。
- Path Param：
  - session_id: int
- Response：`204 No Content`
- 权限：校验记录是否属于当前用户。

### 5.2. 精力记录 (`/energy-logs`)

#### POST `/`
- 描述：创建新的精力记录。
- Request Body：
```json
schemas.EnergyLogCreate // 包含 timestamp (可选，默认 now), energy_level, source, notes
```
- Response Body：
```json
schemas.EnergyLog // status_code=201
```

#### GET `/`
- 描述：获取当前用户的精力记录。
- Query Params：
  - date_start: Optional[datetime] = None
  - date_end: Optional[datetime] = None
  - skip: int = 0, limit: int = 100 （分页）
- Response Body：
```json
List[schemas.EnergyLog]
```

#### GET `/{log_id}`
- 描述：获取特定精力记录的详情。
- Path Param：
  - log_id: int
- Response Body：
```json
schemas.EnergyLog
```
- 权限：校验记录是否属于当前用户。

#### PUT `/{log_id}`
- 描述：更新特定精力记录。
- Path Param：
  - log_id: int
- Request Body：
```json
schemas.EnergyLogUpdate
```
- Response Body：
```json
schemas.EnergyLog
```
- 权限：校验记录是否属于当前用户。

#### DELETE `/{log_id}`
- 描述：删除特定精力记录。
- Path Param：
  - log_id: int
- Response：`204 No Content`
- 权限：校验记录是否属于当前用户。

### 5.3. 报告 (`/reports`)

#### GET `/energy`
- 描述：获取精力报告数据（例如按天/周聚合的平均精力水平）。
- Query Params：
  - period: str = "daily" / "weekly"
  - date_start: datetime
  - date_end: datetime
- Response Body：
```json
schemas.EnergyReport // 包含聚合数据和图表所需格式
```

#### GET `/task-completion`
- 描述：获取任务完成报告数据（例如已完成任务数、平均完成时长）。
- Query Params：
  - period: str = "daily" / "weekly"
  - date_start: datetime
  - date_end: datetime
  - project_id: Optional[int] = None
- Response Body：
```json
schemas.TaskCompletionReport
```

#### GET `/screen-time`（如果实现屏幕时间监控）
- 描述：获取屏幕时间报告数据。
- Query Params：
  - period: str = "daily" / "weekly"
  - date_start: datetime
  - date_end: datetime
- Response Body：
```json
schemas.ScreenTimeReport
```

## 6. AI 服务 API (`/api/ai`)

> 这些端点可能直接调用外部 LLM API 或内部 AI 逻辑。

#### POST `/decompose-task`
- 描述：请求 AI 分解任务。
- Request Body：
```json
schemas.AIDecomposeTaskRequest // 包含 task_id (可选，用于上下文), task_title, task_description (可选), user_prompt (可选，用户具体要求)
```
- Response Body：
```json
schemas.AIDecomposeTaskResponse // 包含 original_task_id (可选), subtasks: List[schemas.AISubtask], ai_notes: Optional[str]
```
- AISubtask schema：
```json
{ "title": str, "description": Optional[str], "priority": Optional[str] }
```
- 逻辑：构造 prompt -> 调用 LLM -> 解析响应 -> （可选）将分解的子任务存入数据库或仅返回给前端由用户确认。

#### POST `/schedule-day`
- 描述：请求 AI 规划一天/一周的日程。
- Request Body：
```json
schemas.AIScheduleDayRequest // 包含 date: date, tasks_to_schedule: List[schemas.TaskBasicInfo], user_preferences: schemas.UserPreferencesForAI, current_energy_level: Optional[int]
```
- TaskBasicInfo schema：
```json
{ "task_id": int, "title": str, "priority": int, "due_date": Optional[datetime], "estimated_duration_minutes": Optional[int] }
```
- UserPreferencesForAI schema：
```json
{ "working_hours_start": time, "working_hours_end": time, "prefer_morning_focus": bool, ... }
```
- Response Body：
```json
schemas.AIScheduleDayResponse // 包含 scheduled_tasks: List[schemas.AIScheduledTask], warnings: Optional[List[str]]
```
- AIScheduledTask schema：
```json
{ "task_id": int, "start_time": datetime, "end_time": datetime }
```

#### POST `/estimate-energy`
- 描述：请求 AI 预估用户当前精力水平。
- Request Body：
```json
schemas.AIEstimateEnergyRequest // 包含 recent_activity_summary: Optional[str], recent_tasks_completed: Optional[int], time_of_day: datetime, user_self_reported_energy: Optional[int]
```
- Response Body：
```json
schemas.AIEstimateEnergyResponse // 包含 estimated_energy_level: int (1-5), confidence: Optional[float]
```

---

> 这份 API 列表应该比较完整了。在实际开发中，您可能还会根据具体需求进行微调或添加新的端点。
