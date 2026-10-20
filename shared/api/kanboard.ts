/**
 * Kanboard API Client
 * Shared between web and mobile apps
 */

import type {
  Story,
  Epic,
  Agent,
  Worker,
  Project,
  Sprint,
  Comment,
  ApiResponse,
  ValidationResult,
  SkillProgress,
} from '../types';

// API configuration
export interface KanboardApiConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

// Default configuration
const defaultConfig: KanboardApiConfig = {
  baseUrl: 'http://kanboard.hr-project-tracking.svc.cluster.local',
  timeout: 30000,
};

/**
 * Kanboard API Client
 */
export class KanboardApi {
  private config: KanboardApiConfig;

  constructor(config: Partial<KanboardApiConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
  }

  private async request<T>(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}`,
        };
      }

      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // Stories
  async listStories(params?: {
    column?: string;
    project?: string;
    assignee?: string;
  }): Promise<ApiResponse<Story[]>> {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<Story[]>('GET', `/api/stories${query ? `?${query}` : ''}`);
  }

  async getStory(id: string): Promise<ApiResponse<Story>> {
    return this.request<Story>('GET', `/api/stories/${id}`);
  }

  async createStory(story: Partial<Story>): Promise<ApiResponse<Story>> {
    return this.request<Story>('POST', '/api/stories', story);
  }

  async updateStory(id: string, updates: Partial<Story>): Promise<ApiResponse<Story>> {
    return this.request<Story>('PATCH', `/api/stories/${id}`, updates);
  }

  async moveStory(id: string, column: string): Promise<ApiResponse<Story>> {
    return this.request<Story>('POST', `/api/stories/${id}/move`, { column });
  }

  // Comments (with agent-in-comments support)
  async addComment(
    storyId: string,
    content: string,
    mentions?: string[]
  ): Promise<ApiResponse<Comment>> {
    return this.request<Comment>('POST', `/api/stories/${storyId}/comments`, {
      content,
      mentions,
    });
  }

  async listComments(storyId: string): Promise<ApiResponse<Comment[]>> {
    return this.request<Comment[]>('GET', `/api/stories/${storyId}/comments`);
  }

  // Agent responses (agent-in-comments feature)
  async triggerAgentResponse(
    storyId: string,
    commentId: string,
    agentId: string
  ): Promise<ApiResponse<{ execution_id: string }>> {
    return this.request<{ execution_id: string }>(
      'POST',
      `/maestro/stories/${storyId}/comments/${commentId}/agent-response`,
      { agent_id: agentId }
    );
  }

  // Epics
  async listEpics(projectId?: string): Promise<ApiResponse<Epic[]>> {
    const query = projectId ? `?project=${projectId}` : '';
    return this.request<Epic[]>('GET', `/api/epics${query}`);
  }

  async getEpic(id: string): Promise<ApiResponse<Epic>> {
    return this.request<Epic>('GET', `/api/epics/${id}`);
  }

  async createEpic(epic: Partial<Epic>): Promise<ApiResponse<Epic>> {
    return this.request<Epic>('POST', '/api/epics', epic);
  }

  // Agents
  async listAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('GET', '/maestro/agents');
  }

  async getAgentStatus(id: string): Promise<ApiResponse<Agent>> {
    return this.request<Agent>('GET', `/maestro/agents/${id}`);
  }

  // Workers
  async listWorkers(): Promise<ApiResponse<Worker[]>> {
    return this.request<Worker[]>('GET', '/maestro/workers');
  }

  async getWorkerStatus(id: string): Promise<ApiResponse<Worker>> {
    return this.request<Worker>('GET', `/maestro/workers/${id}`);
  }

  async registerWorker(worker: Partial<Worker>): Promise<ApiResponse<Worker>> {
    return this.request<Worker>('POST', '/maestro/workers', worker);
  }

  // Projects
  async listProjects(): Promise<ApiResponse<Project[]>> {
    return this.request<Project[]>('GET', '/api/projects');
  }

  async getProject(id: string): Promise<ApiResponse<Project>> {
    return this.request<Project>('GET', `/api/projects/${id}`);
  }

  // Sprints
  async listSprints(projectId: string): Promise<ApiResponse<Sprint[]>> {
    return this.request<Sprint[]>('GET', `/api/projects/${projectId}/sprints`);
  }

  async getCurrentSprint(projectId: string): Promise<ApiResponse<Sprint | null>> {
    return this.request<Sprint | null>('GET', `/api/projects/${projectId}/sprints/current`);
  }

  // Validation
  async getValidationResult(storyId: string): Promise<ApiResponse<ValidationResult | null>> {
    return this.request<ValidationResult | null>(
      'GET',
      `/maestro/stories/${storyId}/validation`
    );
  }

  async triggerValidation(storyId: string): Promise<ApiResponse<{ execution_id: string }>> {
    return this.request<{ execution_id: string }>(
      'POST',
      `/maestro/stories/${storyId}/validate`
    );
  }

  // Skills
  async getSkillProgress(storyId: string): Promise<ApiResponse<SkillProgress>> {
    return this.request<SkillProgress>('GET', `/maestro/stories/${storyId}/skills`);
  }

  async executeSkill(
    storyId: string,
    skill: string
  ): Promise<ApiResponse<{ execution_id: string }>> {
    return this.request<{ execution_id: string }>(
      'POST',
      `/maestro/stories/${storyId}/skills/${skill}/execute`
    );
  }
}

// Singleton instance
let apiInstance: KanboardApi | null = null;

export function getKanboardApi(config?: Partial<KanboardApiConfig>): KanboardApi {
  if (!apiInstance || config) {
    apiInstance = new KanboardApi(config);
  }
  return apiInstance;
}
