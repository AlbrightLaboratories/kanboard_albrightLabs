/**
 * Kanboard JSON-RPC Client
 *
 * Wrapper for Kanboard's JSON-RPC API with error handling.
 */

export interface KanboardStory {
  id: number;
  title: string;
  description: string;
  project_id: number;
  column_id: number;
  owner_id: number;
  creator_id: number;
  date_creation: number;
  date_modification: number;
  date_moved: number;
  position: number;
  is_active: number;
  category_id: number;
  swimlane_id: number;
  color_id: string;
  priority: number;
  score: number;
  reference: string;
  date_started: number | null;
  date_due: number | null;
  time_estimated: number;
  time_spent: number;
}

export interface KanboardProject {
  id: number;
  name: string;
  description: string;
  is_active: number;
}

export interface KanboardColumn {
  id: number;
  title: string;
  position: number;
  project_id: number;
  task_limit: number;
}

export interface RPCResponse<T> {
  jsonrpc: string;
  id: number;
  result?: T;
  error?: {
    code: number;
    message: string;
  };
}

export class KanboardError extends Error {
  constructor(
    message: string,
    public code?: number,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'KanboardError';
  }
}

export class KanboardClient {
  private endpoint: string;
  private username: string;
  private token: string;
  private requestId: number = 0;
  private timeout: number;

  constructor(config?: {
    endpoint?: string;
    username?: string;
    token?: string;
    timeout?: number;
  }) {
    this.endpoint = config?.endpoint || process.env.KANBOARD_URL || 'http://localhost/jsonrpc.php';
    this.username = config?.username || process.env.KANBOARD_USER || 'admin';
    this.token = config?.token || process.env.KANBOARD_TOKEN || '';
    this.timeout = config?.timeout || 30000;
  }

  /**
   * Make a JSON-RPC request to Kanboard
   */
  async call<T>(method: string, params?: Record<string, unknown>): Promise<T> {
    const id = ++this.requestId;
    const auth = Buffer.from(`${this.username}:${this.token}`).toString('base64');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth}`
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method,
          id,
          params: params || {}
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new KanboardError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response.status >= 500 || response.status === 429
        );
      }

      const data = await response.json() as RPCResponse<T>;

      if (data.error) {
        throw new KanboardError(
          data.error.message,
          data.error.code,
          false
        );
      }

      return data.result as T;
    } catch (error) {
      if (error instanceof KanboardError) {
        throw error;
      }
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new KanboardError('Request timeout', undefined, true);
        }
        if (error.message.includes('ECONNREFUSED') ||
            error.message.includes('ENOTFOUND') ||
            error.message.includes('fetch failed')) {
          throw new KanboardError(
            `Kanboard API unavailable: ${error.message}`,
            undefined,
            true
          );
        }
      }
      throw new KanboardError(String(error), undefined, false);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Test API connectivity
   */
  async ping(): Promise<boolean> {
    try {
      await this.call<string>('getVersion');
      return true;
    } catch {
      return false;
    }
  }

  // Story operations
  async createStory(
    projectId: number,
    title: string,
    description?: string,
    columnId?: number
  ): Promise<number> {
    return this.call<number>('createTask', {
      project_id: projectId,
      title,
      description: description || '',
      column_id: columnId
    });
  }

  async getStory(storyId: number): Promise<KanboardStory | null> {
    return this.call<KanboardStory | null>('getTask', { task_id: storyId });
  }

  async updateStory(
    storyId: number,
    updates: Partial<Pick<KanboardStory, 'title' | 'description' | 'owner_id' | 'priority'>>
  ): Promise<boolean> {
    return this.call<boolean>('updateTask', {
      id: storyId,
      ...updates
    });
  }

  async moveStory(storyId: number, columnId: number, position?: number): Promise<boolean> {
    const story = await this.getStory(storyId);
    if (!story) {
      throw new KanboardError(`Story ${storyId} not found`, 404, false);
    }
    return this.call<boolean>('moveTaskPosition', {
      project_id: story.project_id,
      task_id: storyId,
      column_id: columnId,
      position: position ?? 1,
      swimlane_id: story.swimlane_id || 0
    });
  }

  async listStories(projectId: number, columnId?: number): Promise<KanboardStory[]> {
    const allStories = await this.call<KanboardStory[]>('getAllTasks', {
      project_id: projectId,
      status_id: 1 // active only
    });

    if (columnId !== undefined) {
      return allStories.filter(s => s.column_id === columnId);
    }
    return allStories;
  }

  // Column operations
  async getColumns(projectId: number): Promise<KanboardColumn[]> {
    return this.call<KanboardColumn[]>('getColumns', { project_id: projectId });
  }

  async getColumnByName(projectId: number, name: string): Promise<KanboardColumn | undefined> {
    const columns = await this.getColumns(projectId);
    return columns.find(c => c.title.toLowerCase() === name.toLowerCase());
  }

  // Project operations
  async getProject(projectId: number): Promise<KanboardProject | null> {
    return this.call<KanboardProject | null>('getProjectById', { project_id: projectId });
  }

  async listProjects(): Promise<KanboardProject[]> {
    return this.call<KanboardProject[]>('getAllProjects');
  }

  // Comment operations
  async addComment(storyId: number, content: string, userId?: number): Promise<number> {
    return this.call<number>('createComment', {
      task_id: storyId,
      content,
      user_id: userId || 0
    });
  }
}

export const kanboardClient = new KanboardClient();
