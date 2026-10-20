/**
 * Test MCP-08: Error handling: Kanboard API down returns graceful error
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { createStory } from '../tools/story/createStory.js';
import { claimStory } from '../tools/agent/claimStory.js';
import { submitForValidation } from '../tools/agent/submitForValidation.js';
import * as kanboardModule from '../clients/kanboardClient.js';
import * as maestroModule from '../clients/maestroClient.js';

// Mock the clients
vi.mock('../clients/kanboardClient.js', () => ({
  kanboardClient: {
    createStory: vi.fn(),
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
    claimStory: vi.fn(),
    submitForValidation: vi.fn(),
    currentAgentId: 'claude-test-agent'
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('API Error Handling', () => {
  const mockKanboard = kanboardModule.kanboardClient as {
    createStory: Mock;
    getStory: Mock;
    getColumnByName: Mock;
    moveStory: Mock;
  };
  const mockMaestro = maestroModule.maestroClient as {
    claimStory: Mock;
    submitForValidation: Mock;
    currentAgentId: string;
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Kanboard API Unavailable', () => {
    it('createStory handles connection refused', async () => {
      mockKanboard.getColumnByName.mockRejectedValue(
        new kanboardModule.KanboardError('Kanboard API unavailable: fetch failed', undefined, true)
      );

      const result = await createStory({
        project_id: 1,
        title: 'Test Story'
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('unavailable');
    });

    it('claimStory handles connection refused', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('Kanboard API unavailable: ECONNREFUSED', undefined, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('unavailable');
    });

    it('submitForValidation handles connection refused', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('Kanboard API unavailable: ENOTFOUND', undefined, true)
      );

      const result = await submitForValidation({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('unavailable');
    });
  });

  describe('Kanboard API Timeout', () => {
    it('createStory handles timeout', async () => {
      mockKanboard.getColumnByName.mockRejectedValue(
        new kanboardModule.KanboardError('Request timeout', undefined, true)
      );

      const result = await createStory({
        project_id: 1,
        title: 'Test Story'
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('timeout');
    });

    it('claimStory handles timeout', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('Request timeout', undefined, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('timeout');
    });
  });

  describe('Kanboard HTTP Errors', () => {
    it('handles 500 Internal Server Error', async () => {
      mockKanboard.createStory.mockRejectedValue(
        new kanboardModule.KanboardError('HTTP 500: Internal Server Error', 500, true)
      );
      mockKanboard.getColumnByName.mockResolvedValue({ id: 1 });

      const result = await createStory({
        project_id: 1,
        title: 'Test Story'
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('500');
    });

    it('handles 503 Service Unavailable', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('HTTP 503: Service Unavailable', 503, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('503');
    });

    it('handles 429 Rate Limited', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('HTTP 429: Too Many Requests', 429, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('429');
    });
  });

  describe('Graceful Error Format', () => {
    it('returns structured error response', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('Connection failed', undefined, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result).toHaveProperty('success', false);
      expect(result).toHaveProperty('error');
      expect(typeof result.error).toBe('string');
    });

    it('error message is human-readable', async () => {
      mockKanboard.getStory.mockRejectedValue(
        new kanboardModule.KanboardError('Kanboard API unavailable: ECONNREFUSED', undefined, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.error).not.toContain('[object Object]');
      expect(result.error).not.toContain('undefined');
    });

    it('handles unknown error types', async () => {
      mockKanboard.getStory.mockRejectedValue('Unknown string error');

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('handles null/undefined errors', async () => {
      mockKanboard.getStory.mockRejectedValue(null);

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
    });
  });

  describe('Maestro API Unavailable', () => {
    it('claimStory handles Maestro down', async () => {
      mockKanboard.getStory.mockResolvedValue({ id: 123, title: 'Test' });
      mockMaestro.claimStory.mockRejectedValue(
        new maestroModule.MaestroError('Maestro API unavailable: fetch failed', undefined, true)
      );

      const result = await claimStory({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('Maestro');
    });

    it('submitForValidation handles Maestro down', async () => {
      mockKanboard.getStory.mockResolvedValue({ id: 123, project_id: 1 });
      mockKanboard.getColumnByName.mockResolvedValue({ id: 4 });
      mockKanboard.moveStory.mockResolvedValue(true);
      mockMaestro.submitForValidation.mockRejectedValue(
        new maestroModule.MaestroError('Maestro API unavailable: ECONNREFUSED', undefined, true)
      );

      const result = await submitForValidation({ story_id: 123 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('Maestro');
    });
  });

  describe('Partial Failures', () => {
    it('submitForValidation moves story even if workflow fails', async () => {
      mockKanboard.getStory.mockResolvedValue({ id: 123, project_id: 1 });
      mockKanboard.getColumnByName.mockResolvedValue({ id: 4 });
      mockKanboard.moveStory.mockResolvedValue(true);
      mockMaestro.submitForValidation.mockResolvedValue({
        success: false,
        error: 'Workflow service unavailable'
      });

      const result = await submitForValidation({ story_id: 123 });

      // Move was called
      expect(mockKanboard.moveStory).toHaveBeenCalled();
      // But overall result is failure due to workflow
      expect(result.success).toBe(false);
      expect(result.error).toContain('Workflow');
    });
  });
});
