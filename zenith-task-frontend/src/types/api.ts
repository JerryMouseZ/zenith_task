// Based on schemas.py from the backend and api.md

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  preferences?: Record<string, any> | null; // JSON stored as string, parsed to object
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface UserCreate {
  email: string;
  password: string;
  full_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, any> | null;
}

export interface UserUpdate {
  email?: string | null;
  full_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, any> | null;
  is_active?: boolean | null;
  is_superuser?: boolean | null;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface PasswordUpdate {
  current_password: string;
  new_password: string;
}

// Generic error structure from FastAPI (can be expanded)
export interface APIErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface APIError {
  detail: string | APIErrorDetail[];
}

// Add other types as they are defined in the plan (Project, Task, etc.)
// For now, focusing on auth.

export interface Project {
  id: number;
  user_id: number;
  name: string;
  description?: string | null;
  color_hex?: string | null;
  view_preference?: string | null; // e.g., 'list', 'kanban'
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
  color_hex?: string | null;
  view_preference?: string | null;
}

export interface ProjectUpdate {
  name?: string | null;
  description?: string | null;
  color_hex?: string | null;
  view_preference?: string | null;
  is_archived?: boolean | null;
}

export interface Task {
  id: number;
  user_id: number;
  project_id?: number | null;
  project?: Project | null; // Added to support embedding project details
  parent_task_id?: number | null;
  title: string;
  description?: string | null;
  status: string; // 'todo', 'inprogress', 'done', etc.
  priority?: number | null; // 0, 1, 2, 3
  due_date?: string | null; // ISO datetime string
  estimated_duration_minutes?: number | null;
  actual_duration_minutes?: number | null;
  order_in_list?: number | null;
  is_recurring: boolean;
  recurrence_pattern?: string | null; // e.g., RRULE string
  ai_notes?: string | null;
  created_at: string;
  updated_at: string;
  tags?: Tag[]; // Assuming tags might be nested
  sub_tasks?: Task[]; // Assuming sub_tasks might be nested
}

export interface TaskCreate {
  title: string;
  project_id?: number | null;
  parent_task_id?: number | null;
  description?: string | null;
  status?: string;
  priority?: number | null;
  due_date?: string | null;
  estimated_duration_minutes?: number | null;
  is_recurring?: boolean;
  recurrence_pattern?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  project_id?: number | null; // Allow moving task between projects
  parent_task_id?: number | null; // Allow changing parent
  description?: string | null;
  status?: string | null;
  priority?: number | null;
  due_date?: string | null;
  estimated_duration_minutes?: number | null;
  actual_duration_minutes?: number | null;
  order_in_list?: number | null;
  is_recurring?: boolean | null;
  recurrence_pattern?: string | null;
  ai_notes?: string | null;
}

export interface TaskReorderItem {
  task_id: number;
  new_order_in_list?: number | null;
  new_status?: string | null;
  new_project_id?: number | null; // If moving between projects during reorder (e.g. drag from general to project board)
}

export interface Tag {
  id: number;
  user_id: number;
  name: string;
  color_hex?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TagCreate {
  name: string;
  color_hex?: string | null;
}

export interface TagUpdate {
  name?: string | null;
  color_hex?: string | null;
}

// TaskTag represents the association, not directly used in POST/PUT bodies often,
// but good for typing responses if the join table model is returned.
export interface TaskTag {
  task_id: number;
  tag_id: number;
}

// Monitoring & Report types from frontend.md
export interface EnergyReportDataPoint {
  time: string; // Or Date object
  level: number;
}
export interface EnergyReport {
  period: string;
  data: EnergyReportDataPoint[];
}

export interface TaskCompletionReportDataPoint {
  period_start: string; // Or Date
  completed_count: number;
  average_time_to_complete?: number; // in minutes or hours
}
export interface TaskCompletionReport {
  period_type: string; // daily, weekly
  data: TaskCompletionReportDataPoint[];
  project_id?: number;
}

// Comment types based on api.md section 4
export interface Comment {
  id: number;
  task_id: number;
  user_id: number;
  content: string;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  user?: User; // Optional: if user details are embedded in the response
}

export interface CommentCreate {
  content: string;
  // task_id will be part of the URL, user_id from auth
}

export interface CommentUpdate {
  content?: string;
}

// Preferences can be generic for now
export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  default_view?: 'kanban' | 'list' | 'calendar';
  ai_prompt_history?: string[];
  [key: string]: any; // For other dynamic preferences
}
