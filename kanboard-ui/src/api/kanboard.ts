/**
 * Kanboard API Client for React Frontend
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
}

export interface Column {
  id: number;
  title: string;
  position: number;
  project_id: number;
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

const API_BASE = import.meta.env.VITE_API_URL || '/api';

class KanboardAPI {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  // Stories
  async getStories(projectId: number): Promise<Story[]> {
    return this.request<Story[]>(`/projects/${projectId}/stories`);
  }

  async moveStory(storyId: number, columnId: number, position?: number): Promise<void> {
    await this.request(`/stories/${storyId}/move`, {
      method: 'POST',
      body: JSON.stringify({ column_id: columnId, position })
    });
  }

  async getStory(storyId: number): Promise<Story> {
    return this.request<Story>(`/stories/${storyId}`);
  }

  async updateStory(storyId: number, updates: Partial<Story>): Promise<void> {
    await this.request(`/stories/${storyId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }

  // Columns
  async getColumns(projectId: number): Promise<Column[]> {
    return this.request<Column[]>(`/projects/${projectId}/columns`);
  }

  // Agents
  async getAgents(): Promise<Agent[]> {
    return this.request<Agent[]>('/agents');
  }

  // Workers
  async getWorkers(): Promise<Worker[]> {
    return this.request<Worker[]>('/workers');
  }

  async registerWorker(worker: Omit<Worker, 'worker_id' | 'status' | 'last_heartbeat'>): Promise<Worker> {
    return this.request<Worker>('/workers', {
      method: 'POST',
      body: JSON.stringify(worker)
    });
  }

  async updateWorkerLabels(storyId: number, labels: string[]): Promise<void> {
    await this.request(`/stories/${storyId}/worker-labels`, {
      method: 'PATCH',
      body: JSON.stringify({ labels })
    });
  }

  async assignWorker(storyId: number, workerId: string): Promise<void> {
    await this.request(`/stories/${storyId}/assign-worker`, {
      method: 'POST',
      body: JSON.stringify({ worker_id: workerId })
    });
  }

  // Validation
  async getValidationResult(storyId: number): Promise<ValidationResult | null> {
    try {
      return await this.request<ValidationResult>(`/stories/${storyId}/validation`);
    } catch {
      return null;
    }
  }

  async triggerRework(storyId: number): Promise<void> {
    await this.request(`/stories/${storyId}/rework`, { method: 'POST' });
  }

  // Skills
  async getSkillProgress(storyId: number): Promise<SkillProgress> {
    return this.request<SkillProgress>(`/stories/${storyId}/skills`);
  }

  // Dependencies
  async getDependencyGraph(storyId: number): Promise<{
    nodes: { id: number; title: string }[];
    edges: { from: number; to: number; type: string }[];
  }> {
    return this.request(`/stories/${storyId}/dependencies`);
  }
}

export const kanboardAPI = new KanboardAPI();
