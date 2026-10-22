/**
 * Tests for Shared Types - SH-01
 *
 * Verifies all Story, Agent, Worker interfaces are exported.
 */

import type {
  // Core entities
  Story,
  Epic,
  Agent,
  Worker,
  Project,
  Sprint,
  Column,
  Comment,
  Subtask,
  Dependency,

  // Status types
  StoryColumn,
  Priority,
  ValidationStatus,
  AgentStatus,
  WorkerStatus,
  SkillStatus,
  MandatorySkill,
  WorkerCapability,

  // Progress/results
  SkillProgress,
  SkillExecution,
  ValidationResult,

  // API
  ApiResponse,
  WebSocketMessage,
  WebSocketMessageType,
} from '../types';

describe('SH-01: Shared types export all Story, Agent, Worker interfaces', () => {
  // Test type existence by creating valid instances
  describe('Story interface', () => {
    it('exports Story with all required fields', () => {
      const story: Story = {
        id: 'story-1',
        title: 'Test Story',
        description: 'A test story',
        column: 'backlog',
        labels: ['bug'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        subtasks: [],
        comments: [],
        skill_progress: {
          plan: { status: 'pending' },
          'design-a-prd': { status: 'pending' },
          tdd: { status: 'pending' },
          'prove-it': { status: 'pending' },
          'release-it': { status: 'pending' },
        },
      };

      expect(story.id).toBe('story-1');
      expect(story.column).toBe('backlog');
    });

    it('supports optional worker fields', () => {
      const story: Story = {
        id: 'story-2',
        title: 'Worker Story',
        description: 'Story with worker assignment',
        column: 'in_progress',
        labels: [],
        worker_labels: ['gpu', 'coding'],
        preferred_worker: 'worker-1',
        excluded_workers: ['worker-2'],
        assigned_worker: 'worker-1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        subtasks: [],
        comments: [],
        skill_progress: {
          plan: { status: 'passed' },
          'design-a-prd': { status: 'in_progress' },
          tdd: { status: 'pending' },
          'prove-it': { status: 'pending' },
          'release-it': { status: 'pending' },
        },
      };

      expect(story.worker_labels).toContain('gpu');
      expect(story.preferred_worker).toBe('worker-1');
    });
  });

  describe('Agent interface', () => {
    it('exports Agent with all required fields', () => {
      const agent: Agent = {
        id: 'agent-1',
        type: 'claude',
        name: 'Claude Code',
        status: 'idle',
        last_heartbeat: new Date().toISOString(),
        capabilities: ['code_generation', 'terminal_execution'],
      };

      expect(agent.type).toBe('claude');
      expect(agent.status).toBe('idle');
    });

    it('supports all agent types', () => {
      const types: Agent['type'][] = ['claude', 'gemini', 'codex', 'custom'];
      types.forEach(type => {
        const agent: Agent = {
          id: `agent-${type}`,
          type,
          name: `Agent ${type}`,
          status: 'idle',
          last_heartbeat: new Date().toISOString(),
          capabilities: [],
        };
        expect(agent.type).toBe(type);
      });
    });
  });

  describe('Worker interface', () => {
    it('exports Worker with all required fields', () => {
      const worker: Worker = {
        id: 'worker-1',
        name: 'Ollama Worker',
        type: 'ollama',
        labels: ['coding', 'fast'],
        endpoint: 'http://ollama:11434',
        auth_method: 'none',
        capabilities: ['code_generation', 'code_review'],
        terminal_enabled: false,
        terminal_sandbox: 'none',
        max_concurrent: 5,
        gpu_required: true,
        gpu_vram_min: 8,
        status: 'active',
        last_heartbeat: new Date().toISOString(),
        active_stories: 0,
      };

      expect(worker.type).toBe('ollama');
      expect(worker.gpu_required).toBe(true);
    });

    it('supports all worker types', () => {
      const types: Worker['type'][] = ['claude', 'gemini', 'codex', 'ollama', 'vllm', 'custom'];
      types.forEach(type => {
        const worker: Worker = {
          id: `worker-${type}`,
          name: `Worker ${type}`,
          type,
          labels: [],
          endpoint: `http://${type}:8080`,
          auth_method: 'api_key',
          capabilities: [],
          terminal_enabled: true,
          terminal_sandbox: 'docker',
          max_concurrent: 1,
          gpu_required: false,
          status: 'idle',
          last_heartbeat: new Date().toISOString(),
          active_stories: 0,
        };
        expect(worker.type).toBe(type);
      });
    });

    it('supports all worker capabilities', () => {
      const capabilities: WorkerCapability[] = [
        'code_generation',
        'code_review',
        'terminal_execution',
        'file_operations',
        'git_operations',
        'test_execution',
        'skill_execution',
        'validation',
      ];

      const worker: Worker = {
        id: 'full-worker',
        name: 'Full Worker',
        type: 'custom',
        labels: [],
        endpoint: 'http://localhost:8080',
        auth_method: 'bearer',
        capabilities,
        terminal_enabled: true,
        terminal_sandbox: 'kubernetes',
        max_concurrent: 10,
        gpu_required: false,
        status: 'active',
        last_heartbeat: new Date().toISOString(),
        active_stories: 3,
      };

      expect(worker.capabilities).toHaveLength(8);
    });
  });

  describe('Supporting interfaces', () => {
    it('exports Project interface', () => {
      const project: Project = {
        id: 'proj-1',
        name: 'Test Project',
        description: 'A test project',
        columns: [
          { id: 'col-1', name: 'Backlog', order: 0 },
          { id: 'col-2', name: 'Done', order: 1 },
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      expect(project.columns).toHaveLength(2);
    });

    it('exports Epic interface', () => {
      const epic: Epic = {
        id: 'epic-1',
        title: 'Test Epic',
        description: 'A test epic',
        stories: ['story-1', 'story-2'],
        status: 'in_progress',
        progress: 50,
      };

      expect(epic.stories).toHaveLength(2);
      expect(epic.progress).toBe(50);
    });

    it('exports Sprint interface', () => {
      const sprint: Sprint = {
        id: 'sprint-1',
        name: 'Sprint 1',
        goal: 'Complete feature X',
        start_date: '2025-01-01',
        end_date: '2025-01-14',
        stories: [],
        status: 'active',
        velocity: 20,
      };

      expect(sprint.status).toBe('active');
    });

    it('exports Dependency interface', () => {
      const dep: Dependency = {
        from_story: 'story-1',
        to_story: 'story-2',
        type: 'blocks',
      };

      expect(dep.type).toBe('blocks');
    });
  });

  describe('Status types', () => {
    it('exports StoryColumn type', () => {
      const columns: StoryColumn[] = ['backlog', 'groomed', 'in_progress', 'validation', 'done'];
      expect(columns).toHaveLength(5);
    });

    it('exports Priority type', () => {
      const priorities: Priority[] = ['critical', 'high', 'medium', 'low'];
      expect(priorities).toHaveLength(4);
    });

    it('exports MandatorySkill type', () => {
      const skills: MandatorySkill[] = ['plan', 'design-a-prd', 'tdd', 'prove-it', 'release-it'];
      expect(skills).toHaveLength(5);
    });
  });

  describe('API types', () => {
    it('exports ApiResponse generic type', () => {
      const successResponse: ApiResponse<Story[]> = {
        success: true,
        data: [],
      };

      const errorResponse: ApiResponse<Story[]> = {
        success: false,
        error: 'Not found',
      };

      expect(successResponse.success).toBe(true);
      expect(errorResponse.success).toBe(false);
    });

    it('exports WebSocketMessage type', () => {
      const message: WebSocketMessage = {
        type: 'progress_update',
        payload: { story_id: '1', progress: 50 },
        timestamp: new Date().toISOString(),
      };

      expect(message.type).toBe('progress_update');
    });
  });
});
