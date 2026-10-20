/**
 * Test MCP-07: kanboard_rework_story picks up failed story for fixing
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { reworkStory } from '../tools/agent/reworkStory.js';
import * as kanboardModule from '../clients/kanboardClient.js';
import * as maestroModule from '../clients/maestroClient.js';

// Mock the clients
vi.mock('../clients/kanboardClient.js', () => ({
  kanboardClient: {
    getStory: vi.fn()
  },
  KanboardError: class KanboardError extends Error {
    constructor(message: string, public code?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'KanboardError';
    }
  }
}));

vi.mock('../clients/maestroClient.js', () => ({
  maestroClient: {
    reworkStory: vi.fn(),
    currentAgentId: 'claude-test-agent'
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('kanboard_rework_story', () => {
  const mockKanboard = kanboardModule.kanboardClient as {
    getStory: Mock;
  };
  const mockMaestro = maestroModule.maestroClient as {
    reworkStory: Mock;
    currentAgentId: string;
  };

  const failureReasons = [
    'test_login_flow failed: AssertionError',
    'Coverage below threshold: 65% < 80%',
    'File auth.py exceeds 200 LOC'
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockKanboard.getStory.mockResolvedValue({
      id: 123,
      title: 'Failed Auth Story',
      description: 'Authentication feature'
    });
    mockMaestro.reworkStory.mockResolvedValue({
      success: true,
      story_id: 123,
      failures: failureReasons
    });
  });

  it('picks up failed story for rework', async () => {
    const result = await reworkStory({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.story_id).toBe(123);
  });

  it('returns failure reasons', async () => {
    const result = await reworkStory({ story_id: 123 });

    expect(result.failures).toBeDefined();
    expect(result.failures).toHaveLength(3);
    expect(result.failures).toContain('test_login_flow failed: AssertionError');
  });

  it('returns story title', async () => {
    const result = await reworkStory({ story_id: 123 });

    expect(result.title).toBe('Failed Auth Story');
  });

  it('returns agent_id', async () => {
    const result = await reworkStory({ story_id: 123 });

    expect(result.agent_id).toBe('claude-test-agent');
  });

  it('verifies story exists', async () => {
    await reworkStory({ story_id: 123 });

    expect(mockKanboard.getStory).toHaveBeenCalledWith(123);
  });

  it('calls Maestro rework API', async () => {
    await reworkStory({ story_id: 123 });

    expect(mockMaestro.reworkStory).toHaveBeenCalledWith(123);
  });

  it('fails if story not found', async () => {
    mockKanboard.getStory.mockResolvedValue(null);

    const result = await reworkStory({ story_id: 999 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('fails without story_id', async () => {
    const result = await reworkStory({ story_id: 0 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('fails if rework not allowed', async () => {
    mockMaestro.reworkStory.mockResolvedValue({
      success: false,
      story_id: 123,
      error: 'Story is not in failed state'
    });

    const result = await reworkStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('not in failed state');
  });

  it('handles Kanboard API errors', async () => {
    mockKanboard.getStory.mockRejectedValue(
      new kanboardModule.KanboardError('Connection timeout', undefined, true)
    );

    const result = await reworkStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Connection timeout');
  });

  it('handles Maestro API errors', async () => {
    mockMaestro.reworkStory.mockRejectedValue(
      new maestroModule.MaestroError('Service unavailable', 503, true)
    );

    const result = await reworkStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Service unavailable');
  });

  it('handles empty failures list', async () => {
    mockMaestro.reworkStory.mockResolvedValue({
      success: true,
      story_id: 123,
      failures: []
    });

    const result = await reworkStory({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.failures).toEqual([]);
  });
});
