# ZenithTask - 前端开发文档 (Next.js)

**版本：** 1.0
**日期：** 2025年6月6日
**项目代号：** ZenithTask
**后端API版本参考：** v1.3 (FastAPI 与 SQLite)

## 目录
1.  引言
2.  技术选型
3.  项目结构
4.  核心页面与组件
    4.1. 认证页面 (Auth Pages)
    4.2. 主看板页面 (Dashboard/Kanban Page)
    4.3. 日历视图页面 (Calendar View Page)
    4.4. 项目视图页面 (Project View & List Page)
    4.5. 任务详情模块 (Task Detail Modal/Pane)
    4.6. 监控与报告页面 (Monitoring & Report Page)
    4.7. 设置页面 (Settings Page)
5.  状态管理
6.  API 交互
7.  UI/UX 设计原则
8.  响应式设计与可访问性

## 1. 引言
本文档详细描述了 Zenith Task 项目前端部分的设计与实现方案。前端将使用 Next.js (React) 框架构建，旨在提供一个现代化、响应式、用户友好的界面，与后端 API (FastAPI + SQLite, v1.3) 进行交互，实现任务管理、监控和 AI 辅助等核心功能。

## 2. 技术选型
* **框架:** Next.js (React) - 支持 SSR, SSG, ISR, API Routes，推荐使用 App Router。
* **语言:** TypeScript。
* **状态管理:**
    * **服务器状态 (API 数据):** SWR / React Query (TanStack Query)。
    * **全局客户端状态:** Zustand 或 Jotai (轻量级选择) / React Context + Hooks (适用于中等复杂度)。
    * **本地组件状态:** `useState`, `useReducer`。
* **UI 库:**
    * **CSS 框架:** Tailwind CSS。
    * **组件基础:** Headless UI / Radix UI。
    * **预构建组件 (推荐):** shadcn/ui (基于 Radix UI 和 Tailwind CSS)。
* **数据请求:** SWR / React Query (内置 fetch 或配合 Axios)。
* **表单处理:** React Hook Form / Formik。
* **图表库 (用于报告):** Recharts / Chart.js。
* **拖拽库 (用于看板):** dnd-kit (推荐，更现代) / react-beautiful-dnd。
* **日历库:** react-big-calendar / FullCalendar (React wrapper)。
* **测试:** Jest, React Testing Library, Cypress (E2E)。
* **代码规范与格式化:** ESLint, Prettier。

## 3. 项目结构 (基于 Next.js App Router)
```text
/app/(app)/                      # 受保护的路由组 (需要认证)
  dashboard/page.tsx            # 主看板页面
  calendar/page.tsx             # 日历视图页面
  projects/page.tsx             # 项目列表页面
  [projectId]/page.tsx          # 特定项目视图页面
  monitoring/page.tsx           # 监控与报告页面
  settings/page.tsx             # 设置页面
  layout.tsx                    # (app) 路由组的布局 (包含侧边栏、导航栏等)

/(auth)/                        # 认证路由组
  login/page.tsx                # 登录页面
  signup/page.tsx               # 注册页面
  layout.tsx                    # (auth) 路由组的布局

/api/                           # Next.js API Routes (如果前端需要 BFF 层，或用于 NextAuth.js)
  auth/[...nextauth]/route.ts   # NextAuth.js 认证路由 (如果使用)

/components/
  /ui/                          # 可复用的基础 UI 组件 (来自 shadcn/ui 或自定义)
    # e.g., Button.tsx, Input.tsx, Card.tsx, Modal.tsx
  /layout/                      # 布局相关组件 (e.g., Sidebar.tsx, Navbar.tsx, PageWrapper.tsx)
  /features/                    # 特定功能模块的组件
    /auth/LoginForm.tsx, SignupForm.tsx
    /kanban/KanbanBoard.tsx, KanbanColumn.tsx, KanbanCard.tsx, TaskQuickAddForm.tsx
    /calendar/EventCalendar.tsx
    /project/ProjectList.tsx, ProjectCard.tsx, ProjectForm.tsx
    /task/TaskForm.tsx, TaskDetailView.tsx, SubtaskList.tsx
    /monitoring/EnergyChart.tsx, TaskCompletionChart.tsx
    /settings/ProfileForm.tsx, PreferencesForm.tsx

/lib/                           # 辅助函数、常量、API 客户端等
  apiClient.ts                  # 配置好的 API 请求客户端 (Axios 实例或 fetch 包装器)
  authOptions.ts                # NextAuth.js 配置 (如果使用)
  utils.ts                      # 通用工具函数 (日期格式化、数据转换等)
  hooks/                        # 自定义 React Hooks (e.g., useCurrentUser.ts)
  constants.ts                  # 应用常量 (如 API 基础路径, 事件名等)

/store/                         # 全局状态管理 (Zustand stores 或 Jotai atoms)
  userStore.ts
  uiStore.ts

/styles/                        # 全局样式, Tailwind CSS 配置
globals.css

/public/                        # 静态资源 (图片、字体等)

/types/                         # TypeScript 类型定义
  api.ts                        # 后端 API 请求和响应的类型 (对应后端的 schemas.py)
  index.ts                      # 应用内部的通用类型

next.config.js
tailwind.config.ts
tsconfig.json
...（省略部分其他配置或脚本文件）
```

## 4. 核心页面与组件

### 4.1. 认证页面 (Auth Pages) (`/app/(auth)/*`)

#### 4.1.1. 登录页面 (`/app/(auth)/login/page.tsx`)
* **组件:** `features/auth/LoginForm.tsx`
* **功能:** 提供邮箱和密码输入进行登录。
* **状态:** 表单输入值、加载状态、错误信息。
* **API 交互:**
    * **POST `/api/auth/token`**: 使用 `username` (邮箱) 和 `password`。
        * 成功: 保存返回的 `access_token` (例如在 HttpOnly Cookie 或安全存储中)，重定向到主看板页面 (`/dashboard`)。
        * 失败: 显示错误信息。

#### 4.1.2. 注册页面 (`/app/(auth)/signup/page.tsx`)
* **组件:** `features/auth/SignupForm.tsx`
* **功能:** 提供邮箱、密码、全名等信息进行用户注册。
* **状态:** 表单输入值、加载状态、错误信息、密码确认。
* **API 交互:**
    * **POST `/api/auth/register`**: 提交 `schemas.UserCreate` 数据。
        * 成功: 自动登录或提示用户登录，重定向到主看板页面或登录页。
        * 失败: 显示错误信息 (例如邮箱已存在)。

### 4.2. 主看板页面 (Dashboard/Kanban Page) (`/app/(app)/dashboard/page.tsx`)
* **组件:** `features/kanban/KanbanBoard.tsx`, `KanbanColumn.tsx`, `KanbanCard.tsx`, `TaskQuickAddForm.tsx`。
* **布局:** 侧边栏导航、顶部导航栏 (用户菜单、全局快速添加任务按钮)、主内容区为看板。
* **功能:**
    * 按状态（例如 'todo', 'inprogress', 'done'）分组显示任务列。
    * 任务卡片支持拖拽，可在列间移动（改变状态）或列内排序。
    * 每列或全局可快速添加任务。
    * 提供任务筛选功能 (按项目、标签、优先级、截止日期等)。
    * 任务卡片点击后打开任务详情模块。
* **状态:**
    * 任务列表 (通过 SWR/React Query 管理，来自 API)。
    * 看板列定义 (可以是固定的，或用户可配置)。
    * 筛选条件、排序方式。
    * 拖拽状态。
    * 加载状态、错误状态。
* **API 交互:**
    * **GET `/api/tasks`**: 获取用户任务。
        * Query Params: 可根据筛选条件动态添加，例如 `status`, `project_id`, `priority`, `due_date_start`, `due_date_end`, `tags`。
    * **PUT `/api/tasks/reorder`**: 任务拖拽完成后调用，批量更新任务的 `order_in_list` 和 `status`。
        * Request Body: `List[schemas.TaskReorderItem]`。
    * **POST `/api/tasks`**: 通过快速添加表单创建新任务。
        * Request Body: `schemas.TaskCreate`。

### 4.3. 日历视图页面 (Calendar View Page) (`/app/(app)/calendar/page.tsx`)
* **组件:** `features/calendar/EventCalendar.tsx` (使用 `react-big-calendar` 或 `FullCalendar`)。
* **功能:**
    * 在月/周/日视图中显示带截止日期的任务。
    * 支持拖拽任务调整截止日期。
    * 点击任务事件打开任务详情模块。
    * 支持点击日期/时间槽创建新任务。
* **状态:**
    * 任务列表 (同看板页，可共享 SWR/React Query缓存)。
    * 日历当前视图 (月/周/日)、当前选中日期。
* **API 交互:**
    * **GET `/api/tasks`**: 获取任务，特别是需要 `due_date` 字段。
    * **PUT `/api/tasks/{task_id}`**: 拖拽任务调整截止日期后调用，更新任务的 `due_date`。
        * Request Body: `schemas.TaskUpdate` (仅含 `due_date`)。
    * **POST `/api/tasks`**: 点击日历槽位创建新任务时调用。

### 4.4. 项目视图与列表页面 (`/app/(app)/projects/*`)

#### 4.4.1. 项目列表页面 (`/app/(app)/projects/page.tsx`)
* **组件:** `features/project/ProjectList.tsx`, `ProjectCard.tsx`, `ProjectForm.tsx` (用于创建新项目)。
* **功能:**
    * 展示用户的所有项目列表。
    * 允许创建新项目。
    * 点击项目卡片导航到特定项目视图页面。
* **状态:**
    * 项目列表 (通过 SWR/React Query 管理)。
    * 创建项目表单的显隐与状态。
* **API 交互:**
    * **GET `/api/projects`**: 获取用户所有项目。
        * Query Params: `archived: false` (默认)。
    * **POST `/api/projects`**: 创建新项目。
        * Request Body: `schemas.ProjectCreate`。

#### 4.4.2. 特定项目视图页面 (`/app/(app)/projects/[projectId]/page.tsx`)
* **组件:** 类似主看板页面，但数据源限定于特定项目，例如 `features/kanban/KanbanBoard.tsx` (传入 `projectId` prop)。
* **功能:**
    * 显示特定项目下的任务，通常以看板或列表形式。
    * 展示项目详情、允许编辑项目信息。
    * 包含项目相关的设置或操作。
* **状态:**
    * 当前项目详情 (通过 SWR/React Query 管理)。
    * 该项目下的任务列表 (通过 SWR/React Query 管理)。
* **API 交互:**
    * **GET `/api/projects/{projectId}`**: 获取项目详情。
    * **PUT `/api/projects/{projectId}`**: 更新项目详情。
        * Request Body: `schemas.ProjectUpdate`。
    * **GET `/api/tasks`**: 获取该项目下的任务。
        * Query Params: `project_id={projectId}`。
    * (删除项目不在此页面，通常在项目列表或项目设置中有此操作)
        * **DELETE `/api/projects/{projectId}`**

### 4.5. 任务详情模块 (Task Detail Modal/Pane)
* **组件:** `features/task/TaskDetailView.tsx`, `TaskForm.tsx` (用于编辑), `SubtaskList.tsx`。
* **触发方式:** 通常在看板卡片、日历事件、列表项点击时以模态框或侧边栏形式弹出。
* **功能:**
    * 显示任务完整信息: 标题、描述 (富文本)、状态、优先级、截止日期、所属项目、标签、子任务、实际耗时、AI 笔记等。
    * 允许编辑任务的各个字段。
    * 管理子任务 (添加、编辑、删除、标记完成)。
    * 添加/管理标签。
* **状态:**
    * 当前选中并加载的任务数据 (可通过 SWR/React Query 获取或从父组件传递)。
    * 编辑模式的开关状态。
    * 子任务列表状态。
* **API 交互:**
    * **GET `/api/tasks/{task_id}`**: (如果需要单独加载或刷新) 获取任务详情。
    * **PUT `/api/tasks/{task_id}`**: 更新任务信息。
        * Request Body: `schemas.TaskUpdate`。
    * **POST `/api/tasks/{task_id}/subtasks`**: 创建子任务。
        * Request Body: `schemas.TaskCreate`。
    * **PUT `/api/tasks/{subtask_id}`**: 更新子任务 (作为普通任务更新)。
    * **DELETE `/api/tasks/{subtask_id}`**: 删除子任务。
    * **POST `/api/tasks/{task_id}/tags/{tag_id}`**: 为任务添加标签。
    * **DELETE `/api/tasks/{task_id}/tags/{tag_id}`**: 从任务移除标签。
    * **GET `/api/tags`**: 获取用户所有标签列表，用于标签选择器。

### 4.6. 监控与报告页面 (`/app/(app)/monitoring/page.tsx`)
* **组件:** `features/monitoring/EnergyChart.tsx`, `TaskCompletionChart.tsx`, `ScreenTimeChart.tsx` (如果实现)。
* **功能:**
    * 图表展示用户精力预估趋势。
    * 图表/列表展示任务完成统计 (例如每日/每周完成数，平均耗时)。
    * (如果实现) 图表展示屏幕时间使用分析 (高效 vs 分心应用/网站)。
* **状态:**
    * 聚合后的报告数据 (通过 SWR/React Query 管理)。
    * 图表配置 (例如时间范围选择器)。
* **API 交互:**
    * **GET `/api/monitoring/reports/energy`**: 获取精力报告数据。
        * Query Params: `period`, `date_start`, `date_end`。
    * **GET `/api/monitoring/reports/task-completion`**: 获取任务完成报告。
        * Query Params: `period`, `date_start`, `date_end`, `project_id` (可选)。
    * **GET `/api/monitoring/reports/screen-time`**: (如果实现) 获取屏幕时间报告。
    * **POST `/api/monitoring/focus-sessions`**: (如果在此页面有手动添加专注时段功能)
        * Request Body: `schemas.FocusSessionCreate`。
    * **POST `/api/monitoring/energy-logs`**: (如果在此页面有手动记录精力功能)
        * Request Body: `schemas.EnergyLogCreate`。

### 4.7. 设置页面 (`/app/(app)/settings/page.tsx`)
* **组件:** `features/settings/ProfileForm.tsx`, `PreferencesForm.tsx`, `PasswordChangeForm.tsx`。
* **功能:**
    * 用户个人资料修改 (全名、头像)。
    * 密码修改。
    * 应用偏好设置 (主题 - 暗/亮模式，默认视图，通知开关)。
    * AI 相关设置 (例如默认提示模板，数据使用授权等)。
* **状态:**
    * 当前用户数据 (通过 SWR/React Query 管理)。
    * 各表单的输入值、加载、错误状态。
* **API 交互:**
    * **GET `/api/users/me`**: 获取当前用户信息。
    * **PUT `/api/users/me`**: 更新用户资料。
        * Request Body: `schemas.UserUpdate`。
    * **PUT `/api/users/me/password`**: 修改密码。
        * Request Body: `schemas.PasswordUpdate`。
    * **GET `/api/users/me/preferences`**: 获取用户偏好。
    * **PUT `/api/users/me/preferences`**: 更新用户偏好。
        * Request Body: `Dict[str, Any]`。

## 5. 状态管理

* **服务器状态 (API 数据):**
    * **SWR 或 React Query (TanStack Query)** 将作为首选，用于管理从后端获取的数据。
    * 它们提供缓存、自动重新验证、乐观更新、分页和无限滚动等强大功能。
    * 例如: `const { data: tasks, error, isLoading, mutate } = useSWR('/api/tasks', apiClient.get);`
* **全局客户端状态:**
    * **Zustand 或 Jotai:** 用于管理与 API 无直接关联的全局状态，如：
        * UI 主题 (暗/亮模式)。
        * 侧边栏的展开/折叠状态。
        * 全局通知消息。
        * 当前活动的模态框状态。
    * **React Context + useReducer:** 适用于中等复杂度的共享状态，如果不想引入额外库。
* **本地组件状态:**
    * `useState` 和 `useReducer` 用于管理组件内部的临时状态，如表单输入、加载指示器、组件内部的显隐切换等。

## 6. API 交互

* **API 客户端 (`/lib/apiClient.ts`):**
    * 创建一个集中的 API 请求客户端。可以使用 `axios` 实例或基于 `fetch` API 的封装。
    * 配置基础 URL (例如从环境变量读取 `NEXT_PUBLIC_API_URL=/api`)。
    * 自动处理认证 Token 的附加 (从存储中读取 JWT 并添加到 `Authorization` header)。
    * 统一处理常见的 API 错误和响应格式。
    ```typescript
    // lib/apiClient.ts (示例使用 fetch)
    import { getToken } from './auth'; // 假设有获取 token 的方法

    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

    async function request<T>(
      endpoint: string,
      options: RequestInit = {}
    ): Promise<T> {
      const token = getToken(); // 获取 JWT
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        // 可以根据 status code 做更细致的错误处理
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(errorData.detail || errorData.message || `API Error: ${response.status}`);
      }

      if (response.status === 204) { // No Content
        return undefined as T;
      }
      return response.json() as Promise<T>;
    }

    export const apiClient = {
      get: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'GET' }),
      post: <T, U>(endpoint: string, body: U, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),
      put: <T, U>(endpoint: string, body: U, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),
      delete: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'DELETE' }),
    };
    ```

* **类型定义 (`/types/api.ts`):**
    * 为所有 API 请求体 (Request Payloads) 和响应体 (Response Bodies) 创建 TypeScript 类型或接口，与后端 `schemas.py` 对应。这有助于在编译时捕获错误并提供更好的开发体验。
    * 例如，对应后端 `schemas.Task`：
    ```typescript
    // types/api.ts
    export interface Task {
      id: number;
      user_id: number;
      project_id?: number | null;
      parent_task_id?: number | null;
      title: string;
      description?: string | null;
      status: string; // 'todo', 'inprogress', 'done', etc.
      priority?: number | null; // 0, 1, 2, 3
      due_date?: string | null; // ISO datetime string
      // ... 其他字段
      created_at: string; // ISO datetime string
      updated_at: string; // ISO datetime string
    }

    export interface TaskCreate {
      title: string;
      project_id?: number | null;
      // ... 其他可创建字段
    }

    export interface TaskUpdate {
      title?: string;
      status?: string;
      // ... 其他可更新字段
    }
    // ... 定义其他所有 schema (User, Project, Tag, etc.)
    ```

* **使用 SWR/React Query 进行数据获取和变更:**
    * **获取数据 (GET):**
        ```typescript
        // 在组件中使用
        import useSWR from 'swr';
        import { apiClient } from '@/lib/apiClient';
        import { Task } from '@/types/api';

        function MyTasksComponent() {
          const { data: tasks, error, isLoading } = useSWR<Task[]>('/tasks', apiClient.get);

          if (isLoading) return <div>加载中...</div>;
          if (error) return <div>加载任务失败: {error.message}</div>;
          // ... 渲染 tasks
        }
        ```
    * **创建数据 (POST):**
        ```typescript
        import useSWRMutation from 'swr/mutation';
        import { apiClient } from '@/lib/apiClient';
        import { Task, TaskCreate } from '@/types/api';

        async function createTask(url: string, { arg }: { arg: TaskCreate }) {
          return apiClient.post<Task, TaskCreate>(url, arg);
        }

        function AddTaskButton() {
          const { trigger, isMutating } = useSWRMutation('/tasks', createTask);

          const handleAddTask = async () => {
            try {
              const newTaskData = { title: '新任务' /*, 其他字段 */ };
              const result = await trigger(newTaskData);
              console.log('任务已创建:', result);
              // 通常会配合 useSWR 的 mutate 来更新任务列表缓存
            } catch (e) {
              console.error('创建任务失败:', e.message);
            }
          };

          return <button onClick={handleAddTask} disabled={isMutating}>
            {isMutating ? '创建中...' : '添加任务'}
          </button>;
        }
        ```
    * 类似的模式适用于 PUT 和 DELETE 请求。React Query (TanStack Query) 也有类似的 `useQuery` 和 `useMutation` hooks。

## 7. UI/UX 设计原则
* **简洁直观 (Simplicity & Intuitiveness):** 界面清晰，导航明确，减少不必要的元素。
* **一致性 (Consistency):** 在整个应用中保持统一的设计语言、组件行为和交互模式。
* **反馈及时 (Feedback):** 对用户的操作（如点击、加载、保存）提供即时的视觉反馈。
* **用户掌控 (Control & Freedom):** 提供撤销操作的可能，允许用户轻松退出当前流程，自定义视图和偏好。
* **减少认知负荷 (Reduce Cognitive Load):** 提供智能默认值，逐步展示信息，保持清晰的视觉层级。
* **美观与愉悦 (Aesthetics & Delight):** 追求现代化的视觉设计，适当使用动画和微交互提升用户体验。

## 8. 响应式设计与可访问性 (A11y)
* **响应式设计:**
    * 使用 Tailwind CSS 的响应式断点 (`sm:`, `md:`, `lg:`, `xl:`) 确保应用在桌面、平板和移动设备上均有良好表现。
    * 针对不同屏幕尺寸优化布局、字体大小和交互元素。
* **可访问性 (A11y):**
    * 使用语义化的 HTML 标签。
    * 为交互元素提供适当的 ARIA 属性 (例如 `aria-label`, `role`)。
    * 确保所有功能都可以通过键盘操作。
    * 保持足够的色彩对比度，符合 WCAG 标准。
    * 管理焦点，特别是在模态框和动态内容中。
    * 使用 `eslint-plugin-jsx-a11y` 等工具进行检查。
