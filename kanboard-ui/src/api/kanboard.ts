/**
 * Kanboard API Client for React Frontend
 * Uses Kanboard's native JSON-RPC API
 */

export interface Story {
  id: number;
  title: string;
  description: string;
  column_id: number;
  project_id: number;
  owner_id: number;
  priority: number;
  position: number;
  worker_labels?: string[];
  assigned_worker?: string;
  color_id?: string;
  date_due?: number;
  is_active?: number;
}

export interface Column {
  id: number;
  title: string;
  position: number;
  project_id: number;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  is_active: number;
}

export interface Agent {
  agent_id: string;
  agent_type: string;
  status: 'idle' | 'working' | 'validating' | 'blocked';
  current_story?: number;
  last_heartbeat: number;
}

export interface Worker {
  worker_id: string;
  name: string;
  type: string;
  labels: string[];
  status: 'active' | 'idle' | 'busy' | 'offline' | 'error';
  last_heartbeat: number;
  capabilities: string[];
}

export interface ValidationResult {
  story_id: number;
  status: 'passed' | 'failed';
  failures?: string[];
  timestamp: number;
}

export interface SkillProgress {
  story_id: number;
  skills: {
    name: string;
    status: 'pending' | 'running' | 'passed' | 'failed';
  }[];
}

// Kanboard JSON-RPC endpoint - proxied through nginx to avoid CORS
const KANBOARD_URL = import.meta.env.VITE_KANBOARD_URL || '/jsonrpc.php';
const KANBOARD_USER = import.meta.env.VITE_KANBOARD_USER || 'admin';
const KANBOARD_PASSWORD = import.meta.env.VITE_KANBOARD_PASSWORD || 'admin';

class KanboardAPI {
  private requestId = 0;

  private async jsonRpc<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    this.requestId++;

    const auth = btoa(`${KANBOARD_USER}:${KANBOARD_PASSWORD}`);

    const response = await fetch(KANBOARD_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth}`
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method,
        id: this.requestId,
        params
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      throw new Error(`Kanboard API error: ${data.error.message || JSON.stringify(data.error)}`);
    }

    return data.result as T;
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return this.jsonRpc<Project[]>('getAllProjects');
  }

  async getProject(projectId: number): Promise<Project> {
    return this.jsonRpc<Project>('getProjectById', { project_id: projectId });
  }

  // Stories (Tasks in Kanboard terminology)
  async getStories(projectId: number): Promise<Story[]> {
    const tasks = await this.jsonRpc<Story[]>('getAllTasks', {
      project_id: projectId,
      status_id: 1  // Active tasks only
    });
    return tasks || [];
  }

  async getStory(storyId: number): Promise<Story> {
    return this.jsonRpc<Story>('getTask', { task_id: storyId });
  }

  async createStory(projectId: number, title: string, description?: string): Promise<number> {
    return this.jsonRpc<number>('createTask', {
      project_id: projectId,
      title,
      description: description || ''
    });
  }

  async moveStory(storyId: number, columnId: number, position?: number): Promise<boolean> {
    // First move to column
    const moved = await this.jsonRpc<boolean>('moveTaskToColumn', {
      task_id: storyId,
      column_id: columnId
    });

    // Then update position if specified
    if (moved && position !== undefined) {
      await this.jsonRpc<boolean>('moveTaskPosition', {
        project_id: 0, // Will be determined from task
        task_id: storyId,
        column_id: columnId,
        position: position
      });
    }

    return moved;
  }

  async updateStory(storyId: number, updates: Partial<Story>): Promise<boolean> {
    return this.jsonRpc<boolean>('updateTask', {
      id: storyId,
      ...updates
    });
  }

  // Columns
  async getColumns(projectId: number): Promise<Column[]> {
    const columns = await this.jsonRpc<Column[]>('getColumns', { project_id: projectId });
    return columns || [];
  }

  // Agents - requires Maestro backend (not yet deployed)
  async getAgents(): Promise<Agent[]> {
    // Maestro API not deployed yet - return empty array
    console.warn('Agents API not available - Maestro backend not deployed');
    return [];
  }

  // Workers - requires Worker Registry (not yet deployed)
  async getWorkers(): Promise<Worker[]> {
    // Worker Registry not deployed yet - return empty array
    console.warn('Workers API not available - Worker Registry not deployed');
    return [];
  }

  async registerWorker(_worker: Omit<Worker, 'worker_id' | 'status' | 'last_heartbeat'>): Promise<Worker> {
    throw new Error('Worker Registry not deployed yet');
  }

  async updateWorkerLabels(_storyId: number, _labels: string[]): Promise<void> {
    throw new Error('Worker Registry not deployed yet');
  }

  async assignWorker(_storyId: number, _workerId: string): Promise<void> {
    throw new Error('Worker Registry not deployed yet');
  }

  // Validation - requires Maestro backend
  async getValidationResult(_storyId: number): Promise<ValidationResult | null> {
    // Maestro API not deployed yet
    return null;
  }

  async triggerRework(_storyId: number): Promise<void> {
    throw new Error('Maestro backend not deployed yet');
  }

  // Skills - requires Maestro backend
  async getSkillProgress(_storyId: number): Promise<SkillProgress> {
    // Return default pending skills
    return {
      story_id: _storyId,
      skills: [
        { name: 'plan', status: 'pending' },
        { name: 'design-a-prd', status: 'pending' },
        { name: 'tdd', status: 'pending' },
        { name: 'prove-it', status: 'pending' },
        { name: 'release-it', status: 'pending' }
      ]
    };
  }

  // Dependencies - requires Maestro backend
  async getDependencyGraph(_storyId: number): Promise<{
    nodes: { id: number; title: string }[];
    edges: { from: number; to: number; type: string }[];
  }> {
    return { nodes: [], edges: [] };
  }
}

export const kanboardAPI = new KanboardAPI();
