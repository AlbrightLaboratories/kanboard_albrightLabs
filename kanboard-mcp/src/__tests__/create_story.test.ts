/**
 * Test MCP-02: kanboard_create_story tool creates story via API
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { createStory } from '../tools/story/createStory.js';
import * as kanboardModule from '../clients/kanboardClient.js';

// Mock the kanboardClient module
vi.mock('../clients/kanboardClient.js', () => ({
  kanboardClient: {
    createStory: vi.fn(),
    getColumnByName: vi.fn()
  },
  KanboardError: class KanboardError extends Error {
    constructor(message: string, public code?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'KanboardError';
    }
  }
}));

describe('kanboard_create_story', () => {
  const mockClient = kanboardModule.kanboardClient as {
    createStory: Mock;
    getColumnByName: Mock;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient.getColumnByName.mockResolvedValue({ id: 1, title: 'Backlog' });
    mockClient.createStory.mockResolvedValue(123);
  });

  it('creates story with required params', async () => {
    const result = await createStory({
      project_id: 1,
      title: 'Test Story'
    });

    expect(result.success).toBe(true);
    expect(result.story_id).toBe(123);
    expect(mockClient.createStory).toHaveBeenCalledWith(
      1,
      'Test Story',
      undefined,
      1 // Backlog column ID
    );
  });

  it('creates story with description', async () => {
    const result = await createStory({
      project_id: 1,
      title: 'Test Story',
      description: 'Test description with acceptance criteria'
    });

    expect(result.success).toBe(true);
    expect(mockClient.createStory).toHaveBeenCalledWith(
      1,
      'Test Story',
      'Test description with acceptance criteria',
      1
    );
  });

  it('creates story in specified column', async () => {
    mockClient.getColumnByName.mockResolvedValue({ id: 3, title: 'In Progress' });

    const result = await createStory({
      project_id: 1,
      title: 'Test Story',
      column_name: 'In Progress'
    });

    expect(result.success).toBe(true);
    expect(mockClient.getColumnByName).toHaveBeenCalledWith(1, 'In Progress');
    expect(mockClient.createStory).toHaveBeenCalledWith(
      1,
      'Test Story',
      undefined,
      3
    );
  });

  it('defaults to Backlog column', async () => {
    const result = await createStory({
      project_id: 1,
      title: 'Test Story'
    });

    expect(result.success).toBe(true);
    expect(mockClient.getColumnByName).toHaveBeenCalledWith(1, 'Backlog');
  });

  it('fails without project_id', async () => {
    const result = await createStory({
      project_id: 0,
      title: 'Test Story'
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('fails without title', async () => {
    const result = await createStory({
      project_id: 1,
      title: ''
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('handles API errors gracefully', async () => {
    mockClient.createStory.mockRejectedValue(
      new kanboardModule.KanboardError('API error', 500, true)
    );

    const result = await createStory({
      project_id: 1,
      title: 'Test Story'
    });

    expect(result.success).toBe(false);
    expect(result.error).toBe('API error');
  });

  it('works when column not found', async () => {
    mockClient.getColumnByName.mockResolvedValue(undefined);

    const result = await createStory({
      project_id: 1,
      title: 'Test Story'
    });

    expect(result.success).toBe(true);
    expect(mockClient.createStory).toHaveBeenCalledWith(
      1,
      'Test Story',
      undefined,
      undefined
    );
  });

  it('returns story_id on success', async () => {
    mockClient.createStory.mockResolvedValue(456);

    const result = await createStory({
      project_id: 1,
      title: 'New Story'
    });

    expect(result.success).toBe(true);
    expect(result.story_id).toBe(456);
  });
});
