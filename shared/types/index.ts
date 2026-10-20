/**
 * Shared types for Kanboard AlbrightLabs
 * Used by both web (kanboard-ui) and mobile (mobile/) apps
 */

// Story status based on column
export type StoryColumn =
  | 'backlog'
  | 'groomed'
  | 'in_progress'
  | 'validation'
  | 'done';

// Story priority levels
export type Priority = 'critical' | 'high' | 'medium' | 'low';

// Validation status
export type ValidationStatus = 'pending' | 'running' | 'passed' | 'failed';

// Agent status
export type AgentStatus = 'idle' | 'working' | 'validating' | 'blocked' | 'offline';

// Worker status
export type WorkerStatus = 'active' | 'idle' | 'busy' | 'offline' | 'error';

// Skill execution status
export type SkillStatus = 'pending' | 'in_progress' | 'passed' | 'failed';

// Mandatory skills
export type MandatorySkill = 'plan' | 'design-a-prd' | 'tdd' | 'prove-it' | 'release-it';

// Story interface
export interface Story {
  id: string;
  title: string;
  description: string;
  column: StoryColumn;
  assignee?: string;
  reporter?: string;
  labels: string[];
  priority?: Priority;
  estimate?: number;
  epic?: string;
  due_date?: string;
  linked_pr?: string;
  linked_repo?: string;
  linked_branch?: string;
  worker_labels?: string[];
  preferred_worker?: string;
  excluded_workers?: string[];
  assigned_worker?: string;
  created_at: string;
  updated_at: string;
  subtasks: Subtask[];
  comments: Comment[];
  skill_progress: SkillProgress;
  validation_result?: ValidationResult;
}

// Subtask/checklist item
export interface Subtask {
  id: string;
  title: string;
  completed: boolean;
  is_acceptance_criteria: boolean;
  assignee?: string;
  order: number;
}

// Comment on a story
export interface Comment {
  id: string;
  author: string;
  content: string;
  created_at: string;
  is_agent_response: boolean;
  agent_id?: string;
  mentions?: string[];
}

// Skill execution progress
export interface SkillProgress {
  plan: SkillExecution;
  'design-a-prd': SkillExecution;
  tdd: SkillExecution;
  'prove-it': SkillExecution;
  'release-it': SkillExecution;
}

// Individual skill execution
export interface SkillExecution {
  status: SkillStatus;
  started_at?: string;
  completed_at?: string;
  output?: string;
  error?: string;
  agent_id?: string;
}

// Validation result
export interface ValidationResult {
  status: 'passed' | 'failed';
  timestamp: string;
  message: string;
  failures: string[];
  coverage?: number;
  test_count?: number;
  passed_count?: number;
}

// Epic (parent container for stories)
export interface Epic {
  id: string;
  title: string;
  description: string;
  stories: string[];
  owner?: string;
  target_date?: string;
  status: 'not_started' | 'in_progress' | 'done';
  progress: number; // 0-100 percentage
}

// Agent registration
export interface Agent {
  id: string;
  type: 'claude' | 'gemini' | 'codex' | 'custom';
  name: string;
  status: AgentStatus;
  current_story?: string;
  last_heartbeat: string;
  capabilities: string[];
}

// Custom LLM worker
export interface Worker {
  id: string;
  name: string;
  type: 'claude' | 'gemini' | 'codex' | 'ollama' | 'vllm' | 'custom';
  labels: string[];
  endpoint: string;
  auth_method: 'api_key' | 'bearer' | 'mcp' | 'none';
  capabilities: WorkerCapability[];
  terminal_enabled: boolean;
  terminal_sandbox: 'none' | 'docker' | 'kubernetes' | 'firecracker';
  max_concurrent: number;
  gpu_required: boolean;
  gpu_vram_min?: number;
  status: WorkerStatus;
  last_heartbeat: string;
  active_stories: number;
}

// Worker capabilities
export type WorkerCapability =
  | 'code_generation'
  | 'code_review'
  | 'terminal_execution'
  | 'file_operations'
  | 'git_operations'
  | 'test_execution'
  | 'skill_execution'
  | 'validation';

// Dependency between stories
export interface Dependency {
  from_story: string;
  to_story: string;
  type: 'blocks' | 'blocked_by' | 'related';
}

// Project
export interface Project {
  id: string;
  name: string;
  description: string;
  columns: Column[];
  created_at: string;
  updated_at: string;
}

// Column in a project
export interface Column {
  id: string;
  name: string;
  order: number;
  wip_limit?: number;
  color?: string;
}

// Sprint/iteration
export interface Sprint {
  id: string;
  name: string;
  goal: string;
  start_date: string;
  end_date: string;
  stories: string[];
  status: 'planning' | 'active' | 'completed';
  velocity?: number;
}

// API response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// WebSocket message types
export type WebSocketMessageType =
  | 'progress_update'
  | 'validation_result'
  | 'story_moved'
  | 'agent_heartbeat'
  | 'comment_added'
  | 'skill_completed';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload: unknown;
  timestamp: string;
}
