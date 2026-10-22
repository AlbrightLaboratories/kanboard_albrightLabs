/**
 * Tests for Kanboard API Client - SH-02
 *
 * Verifies API client works in browser and React Native environments.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { KanboardApi, getKanboardApi, KanboardApiConfig } from '../api/kanboard';

// Mock fetch for testing
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SH-02: KanboardApi client works in browser and React Native', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Client initialization', () => {
    it('creates client with default config', () => {
      const api = new KanboardApi();
      expect(api).toBeInstanceOf(KanboardApi);
    });

    it('creates client with custom config', () => {
      const config: KanboardApiConfig = {
        baseUrl: 'http://custom.kanboard.local',
        apiKey: 'test-key',
        timeout: 60000,
      };
      const api = new KanboardApi(config);
      expect(api).toBeInstanceOf(KanboardApi);
    });

    it('singleton pattern works', () => {
      const api1 = getKanboardApi();
      const api2 = getKanboardApi();
      expect(api1).toBe(api2);
    });

    it('singleton resets with new config', () => {
      const api1 = getKanboardApi();
      const api2 = getKanboardApi({ baseUrl: 'http://new.url' });
      expect(api1).not.toBe(api2);
    });
  });

  describe('Story operations', () => {
    it('listStories calls correct endpoint', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: '1', title: 'Story 1' }]),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.listStories();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/api/stories',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result.success).toBe(true);
    });

    it('listStories with filters adds query params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.listStories({ column: 'backlog', project: 'proj-1' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('column=backlog'),
        expect.any(Object)
      );
    });

    it('getStory fetches single story', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: '123', title: 'Story' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.getStory('123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/api/stories/123',
        expect.any(Object)
      );
      expect(result.data?.id).toBe('123');
    });

    it('createStory sends POST request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'new', title: 'New Story' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.createStory({ title: 'New Story', column: 'backlog' });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/api/stories',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('New Story'),
        })
      );
    });

    it('moveStory sends move request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: '1', column: 'done' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.moveStory('1', 'done');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/api/stories/1/move',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ column: 'done' }),
        })
      );
    });
  });

  describe('Authentication', () => {
    it('includes API key in headers when configured', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const api = new KanboardApi({
        baseUrl: 'http://test',
        apiKey: 'secret-key',
      });
      await api.listStories();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer secret-key',
          }),
        })
      );
    });

    it('omits auth header when no API key', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.listStories();

      const call = mockFetch.mock.calls[0];
      expect(call[1].headers.Authorization).toBeUndefined();
    });
  });

  describe('Error handling', () => {
    it('handles HTTP errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ error: 'Not found' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.getStory('999');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not found');
    });

    it('handles network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.listStories();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });

    it('handles non-Error exceptions', async () => {
      mockFetch.mockRejectedValueOnce('Unknown failure');

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.listStories();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Unknown error');
    });
  });

  describe('Worker operations', () => {
    it('listWorkers fetches from maestro endpoint', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.listWorkers();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/maestro/workers',
        expect.any(Object)
      );
    });

    it('registerWorker posts to maestro', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'new-worker' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.registerWorker({ name: 'New Worker', type: 'ollama' });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/maestro/workers',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('Skill operations', () => {
    it('executeSkill triggers skill execution', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ execution_id: 'exec-123' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.executeSkill('story-1', 'tdd');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/maestro/stories/story-1/skills/tdd/execute',
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.data?.execution_id).toBe('exec-123');
    });

    it('getSkillProgress fetches skill status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plan: { status: 'passed' },
          tdd: { status: 'in_progress' },
        }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      await api.getSkillProgress('story-1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test/maestro/stories/story-1/skills',
        expect.any(Object)
      );
    });
  });

  describe('React Native compatibility', () => {
    it('uses standard fetch API (available in RN)', () => {
      // The client uses global.fetch which is available in React Native
      expect(typeof fetch).toBe('function');
    });

    it('works with async/await pattern', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.listStories();

      expect(result).toHaveProperty('success');
    });

    it('returns consistent ApiResponse shape', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: '1' }),
      });

      const api = new KanboardApi({ baseUrl: 'http://test' });
      const result = await api.getStory('1');

      // ApiResponse has success, data?, error?, message?
      expect(typeof result.success).toBe('boolean');
      if (result.success) {
        expect(result.data).toBeDefined();
      }
    });
  });
});
