/**
 * Maestro API Client
 *
 * Client for two-way agent communication with the Maestro API.
 */

export interface StoryPrompt {
  story_id: number;
  title: string;
  description: string;
  acceptance_criteria: string[];
  repo_url?: string;
  branch?: string;
  dependencies: number[];
  required_skills: string[];
  context?: string;
}

export interface SkillExecution {
  execution_id: string;
  skill_name: string;
  story_id: number;
  status: 'pending' | 'running' | 'passed' | 'failed';
  output?: unknown;
  error?: string;
}

export interface AgentInfo {
  agent_id: string;
  agent_type: string;
  status: 'idle' | 'working' | 'validating' | 'blocked';
  current_story?: number;
  last_heartbeat: number;
}

export class MaestroError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'MaestroError';
  }
}

export class MaestroClient {
  private endpoint: string;
  private agentId: string;
  private timeout: number;

  constructor(config?: {
    endpoint?: string;
    agentId?: string;
    timeout?: number;
  }) {
    this.endpoint = config?.endpoint || process.env.MAESTRO_URL || 'http://localhost:8080';
    this.agentId = config?.agentId || process.env.AGENT_ID || `claude-${Date.now()}`;
    this.timeout = config?.timeout || 30000;
  }

  /**
   * Make HTTP request to Maestro API
   */
  private async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.endpoint}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-Agent-ID': this.agentId,
          ...options?.headers
        },
        signal: controller.signal
      });

      if (!response.ok) {
        throw new MaestroError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response.status >= 500 || response.status === 429
        );
      }

      return await response.json() as T;
    } catch (error) {
      if (error instanceof MaestroError) {
        throw error;
      }
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new MaestroError('Request timeout', undefined, true);
        }
        if (error.message.includes('ECONNREFUSED') ||
            error.message.includes('fetch failed')) {
          throw new MaestroError(
            `Maestro API unavailable: ${error.message}`,
            undefined,
            true
          );
        }
      }
      throw new MaestroError(String(error), undefined, false);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Register this agent with Maestro
   */
  async register(capabilities?: string[]): Promise<AgentInfo> {
    return this.request<AgentInfo>('/maestro/agents/register', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: this.agentId,
        agent_type: 'claude',
        capabilities: capabilities || ['code_generation', 'skill_execution']
      })
    });
  }

  /**
   * Send heartbeat to keep agent alive
   */
  async heartbeat(): Promise<AgentInfo> {
    return this.request<AgentInfo>(`/maestro/agents/${this.agentId}/heartbeat`);
  }

  /**
   * Claim a story to work on
   */
  async claimStory(storyId: number): Promise<{
    success: boolean;
    story_id: number;
    error?: string;
  }> {
    return this.request('/maestro/stories/claim', {
      method: 'POST',
      body: JSON.stringify({
        story_id: storyId,
        agent_id: this.agentId
      })
    });
  }

  /**
   * Get structured prompt for a story
   */
  async getStoryPrompt(storyId: number): Promise<StoryPrompt> {
    return this.request<StoryPrompt>(`/maestro/stories/${storyId}/prompt`);
  }

  /**
   * Update progress on a story
   */
  async updateProgress(
    storyId: number,
    progress: number,
    message?: string
  ): Promise<{ success: boolean }> {
    return this.request('/maestro/stories/progress', {
      method: 'POST',
      body: JSON.stringify({
        story_id: storyId,
        agent_id: this.agentId,
        progress,
        message
      })
    });
  }

  /**
   * Execute a mandatory skill
   */
  async executeSkill(
    storyId: number,
    skillName: string,
    params?: Record<string, unknown>
  ): Promise<SkillExecution> {
    return this.request<SkillExecution>('/maestro/skills/execute', {
      method: 'POST',
      body: JSON.stringify({
        story_id: storyId,
        skill: skillName,
        agent_id: this.agentId,
        params
      })
    });
  }

  /**
   * Get skill execution status
   */
  async getSkillStatus(executionId: string): Promise<SkillExecution> {
    return this.request<SkillExecution>(`/maestro/skills/${executionId}/status`);
  }

  /**
   * Submit story for validation
   */
  async submitForValidation(storyId: number): Promise<{
    success: boolean;
    workflow_id?: string;
    error?: string;
  }> {
    return this.request('/maestro/stories/validate', {
      method: 'POST',
      body: JSON.stringify({
        story_id: storyId,
        agent_id: this.agentId
      })
    });
  }

  /**
   * Pick up a story for rework after validation failure
   */
  async reworkStory(storyId: number): Promise<{
    success: boolean;
    story_id: number;
    failures?: string[];
    error?: string;
  }> {
    return this.request('/maestro/stories/rework', {
      method: 'POST',
      body: JSON.stringify({
        story_id: storyId,
        agent_id: this.agentId
      })
    });
  }

  get currentAgentId(): string {
    return this.agentId;
  }
}

export const maestroClient = new MaestroClient();
