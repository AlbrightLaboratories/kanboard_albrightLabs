/**
 * Test MCP-03: kanboard_claim_story claims story for Claude agent
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { claimStory } from '../tools/agent/claimStory.js';
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
    claimStory: vi.fn(),
    currentAgentId: 'claude-test-agent'
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('kanboard_claim_story', () => {
  const mockKanboard = kanboardModule.kanboardClient as {
    getStory: Mock;
  };
  const mockMaestro = maestroModule.maestroClient as {
    claimStory: Mock;
    currentAgentId: string;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockKanboard.getStory.mockResolvedValue({
      id: 123,
      title: 'Test Story',
      description: 'Test description'
    });
    mockMaestro.claimStory.mockResolvedValue({
      success: true,
      story_id: 123
    });
  });

  it('claims story successfully', async () => {
    const result = await claimStory({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.story_id).toBe(123);
    expect(result.title).toBe('Test Story');
    expect(result.agent_id).toBe('claude-test-agent');
  });

  it('verifies story exists before claiming', async () => {
    await claimStory({ story_id: 123 });

    expect(mockKanboard.getStory).toHaveBeenCalledWith(123);
  });

  it('calls Maestro API to claim', async () => {
    await claimStory({ story_id: 123 });

    expect(mockMaestro.claimStory).toHaveBeenCalledWith(123);
  });

  it('fails if story not found', async () => {
    mockKanboard.getStory.mockResolvedValue(null);

    const result = await claimStory({ story_id: 999 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('fails without story_id', async () => {
    const result = await claimStory({ story_id: 0 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('fails if already claimed by another agent', async () => {
    mockMaestro.claimStory.mockResolvedValue({
      success: false,
      story_id: 123,
      error: 'Story already claimed by another agent'
    });

    const result = await claimStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('already claimed');
  });

  it('handles Maestro API errors', async () => {
    mockMaestro.claimStory.mockRejectedValue(
      new maestroModule.MaestroError('API unavailable', 503, true)
    );

    const result = await claimStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('API unavailable');
  });

  it('handles Kanboard API errors', async () => {
    mockKanboard.getStory.mockRejectedValue(
      new kanboardModule.KanboardError('Connection refused', undefined, true)
    );

    const result = await claimStory({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Connection refused');
  });

  it('returns agent_id on successful claim', async () => {
    const result = await claimStory({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.agent_id).toBeDefined();
    expect(typeof result.agent_id).toBe('string');
  });
});
