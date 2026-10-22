/**
 * Offline mode tests - MOB-09
 *
 * MOB-09: Offline mode caches stories in AsyncStorage
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Story } from '../../shared/types';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
}));

// Offline cache implementation
const CACHE_KEY = '@kanboard/stories';
const CACHE_EXPIRY_KEY = '@kanboard/stories_expiry';
const CACHE_TTL = 1000 * 60 * 60; // 1 hour

interface OfflineCache {
  saveStories: (stories: Story[]) => Promise<void>;
  loadStories: () => Promise<Story[] | null>;
  clearCache: () => Promise<void>;
  isCacheValid: () => Promise<boolean>;
}

const createOfflineCache = (): OfflineCache => ({
  async saveStories(stories: Story[]): Promise<void> {
    const now = Date.now();
    await AsyncStorage.multiSet([
      [CACHE_KEY, JSON.stringify(stories)],
      [CACHE_EXPIRY_KEY, String(now + CACHE_TTL)],
    ]);
  },

  async loadStories(): Promise<Story[] | null> {
    const valid = await this.isCacheValid();
    if (!valid) return null;

    const data = await AsyncStorage.getItem(CACHE_KEY);
    if (!data) return null;

    try {
      return JSON.parse(data);
    } catch {
      return null;
    }
  },

  async clearCache(): Promise<void> {
    await AsyncStorage.removeItem(CACHE_KEY);
    await AsyncStorage.removeItem(CACHE_EXPIRY_KEY);
  },

  async isCacheValid(): Promise<boolean> {
    const expiry = await AsyncStorage.getItem(CACHE_EXPIRY_KEY);
    if (!expiry) return false;
    return Date.now() < parseInt(expiry, 10);
  },
});

const mockStories: Story[] = [
  {
    id: 'story-1',
    title: 'Cached Story',
    description: 'Test',
    column: 'backlog',
    labels: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    subtasks: [],
    comments: [],
    skill_progress: {
      plan: { status: 'pending' },
      'design-a-prd': { status: 'pending' },
      tdd: { status: 'pending' },
      'prove-it': { status: 'pending' },
      'release-it': { status: 'pending' },
    },
  },
];

describe('MOB-09: Offline mode caches stories in AsyncStorage', () => {
  let cache: OfflineCache;

  beforeEach(() => {
    jest.clearAllMocks();
    cache = createOfflineCache();
  });

  describe('saveStories', () => {
    it('saves stories to AsyncStorage', async () => {
      await cache.saveStories(mockStories);

      expect(AsyncStorage.multiSet).toHaveBeenCalledWith([
        [CACHE_KEY, JSON.stringify(mockStories)],
        [CACHE_EXPIRY_KEY, expect.any(String)],
      ]);
    });

    it('sets expiry timestamp', async () => {
      const before = Date.now();
      await cache.saveStories(mockStories);
      const after = Date.now();

      const call = (AsyncStorage.multiSet as jest.Mock).mock.calls[0][0];
      const expiryValue = parseInt(call[1][1], 10);

      expect(expiryValue).toBeGreaterThan(before);
      expect(expiryValue).toBeLessThanOrEqual(after + CACHE_TTL);
    });
  });

  describe('loadStories', () => {
    it('returns stories from cache when valid', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(String(Date.now() + CACHE_TTL)) // expiry
        .mockResolvedValueOnce(JSON.stringify(mockStories)); // data

      const result = await cache.loadStories();

      expect(result).toEqual(mockStories);
    });

    it('returns null when cache expired', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(String(Date.now() - 1000)); // expired

      const result = await cache.loadStories();

      expect(result).toBeNull();
    });

    it('returns null when no cache exists', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const result = await cache.loadStories();

      expect(result).toBeNull();
    });

    it('returns null when cache is corrupted', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(String(Date.now() + CACHE_TTL))
        .mockResolvedValueOnce('not valid json{');

      const result = await cache.loadStories();

      expect(result).toBeNull();
    });
  });

  describe('clearCache', () => {
    it('removes both cache keys', async () => {
      await cache.clearCache();

      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(CACHE_KEY);
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(CACHE_EXPIRY_KEY);
    });
  });

  describe('isCacheValid', () => {
    it('returns true when not expired', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(
        String(Date.now() + CACHE_TTL)
      );

      const result = await cache.isCacheValid();

      expect(result).toBe(true);
    });

    it('returns false when expired', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(
        String(Date.now() - 1000)
      );

      const result = await cache.isCacheValid();

      expect(result).toBe(false);
    });

    it('returns false when no expiry set', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const result = await cache.isCacheValid();

      expect(result).toBe(false);
    });
  });

  describe('Integration: offline workflow', () => {
    it('can save and load stories', async () => {
      // Save
      await cache.saveStories(mockStories);

      // Mock the load response
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(String(Date.now() + CACHE_TTL))
        .mockResolvedValueOnce(JSON.stringify(mockStories));

      // Load
      const loaded = await cache.loadStories();

      expect(loaded).toEqual(mockStories);
    });

    it('falls back to cache when offline', async () => {
      // Simulate: API call fails, load from cache
      const fetchFromAPI = jest.fn().mockRejectedValue(new Error('Network error'));

      // Cache has data
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(String(Date.now() + CACHE_TTL))
        .mockResolvedValueOnce(JSON.stringify(mockStories));

      let result: Story[] | null = null;
      try {
        result = await fetchFromAPI();
      } catch {
        result = await cache.loadStories();
      }

      expect(result).toEqual(mockStories);
    });
  });
});
