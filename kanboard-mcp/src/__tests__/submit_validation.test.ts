/**
 * Test MCP-06: kanboard_submit_for_validation moves story, triggers workflow
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { submitForValidation } from '../tools/agent/submitForValidation.js';
import * as kanboardModule from '../clients/kanboardClient.js';
import * as maestroModule from '../clients/maestroClient.js';

// Mock the clients
vi.mock('../clients/kanboardClient.js', () => ({
  kanboardClient: {
    getStory: vi.fn(),
    getColumnByName: vi.fn(),
    moveStory: vi.fn()
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
    submitForValidation: vi.fn()
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('kanboard_submit_for_validation', () => {
  const mockKanboard = kanboardModule.kanboardClient as {
    getStory: Mock;
    getColumnByName: Mock;
    moveStory: Mock;
  };
  const mockMaestro = maestroModule.maestroClient as {
    submitForValidation: Mock;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockKanboard.getStory.mockResolvedValue({
      id: 123,
      title: 'Test Story',
      project_id: 1
    });
    mockKanboard.getColumnByName.mockResolvedValue({
      id: 4,
      title: 'Validation'
    });
    mockKanboard.moveStory.mockResolvedValue(true);
    mockMaestro.submitForValidation.mockResolvedValue({
      success: true,
      workflow_id: 'wf-abc-123'
    });
  });

  it('moves story to Validation column', async () => {
    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.column).toBe('Validation');
    expect(mockKanboard.moveStory).toHaveBeenCalledWith(123, 4);
  });

  it('triggers validation workflow', async () => {
    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.workflow_id).toBe('wf-abc-123');
    expect(mockMaestro.submitForValidation).toHaveBeenCalledWith(123);
  });

  it('returns story_id on success', async () => {
    const result = await submitForValidation({ story_id: 123 });

    expect(result.story_id).toBe(123);
  });

  it('fails if story not found', async () => {
    mockKanboard.getStory.mockResolvedValue(null);

    const result = await submitForValidation({ story_id: 999 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('fails if Validation column not found', async () => {
    mockKanboard.getColumnByName.mockResolvedValue(undefined);

    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('Validation column not found');
  });

  it('fails without story_id', async () => {
    const result = await submitForValidation({ story_id: 0 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('fails if workflow trigger fails', async () => {
    mockMaestro.submitForValidation.mockResolvedValue({
      success: false,
      error: 'Workflow trigger failed'
    });

    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('Workflow trigger failed');
  });

  it('looks up Validation column by name', async () => {
    await submitForValidation({ story_id: 123 });

    expect(mockKanboard.getColumnByName).toHaveBeenCalledWith(1, 'Validation');
  });

  it('handles Kanboard move errors', async () => {
    mockKanboard.moveStory.mockRejectedValue(
      new kanboardModule.KanboardError('Move failed', 500, true)
    );

    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Move failed');
  });

  it('handles Maestro API errors', async () => {
    mockMaestro.submitForValidation.mockRejectedValue(
      new maestroModule.MaestroError('API unavailable', 503, true)
    );

    const result = await submitForValidation({ story_id: 123 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('API unavailable');
  });
});
