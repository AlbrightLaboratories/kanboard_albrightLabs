/**
 * Test MCP-04: kanboard_get_story_prompt returns structured prompt
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { getStoryPrompt } from '../tools/agent/getStoryPrompt.js';
import * as maestroModule from '../clients/maestroClient.js';

// Mock the Maestro client
vi.mock('../clients/maestroClient.js', () => ({
  maestroClient: {
    getStoryPrompt: vi.fn()
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('kanboard_get_story_prompt', () => {
  const mockMaestro = maestroModule.maestroClient as {
    getStoryPrompt: Mock;
  };

  const samplePrompt = {
    story_id: 123,
    title: 'Implement user authentication',
    description: 'Add OAuth2 login with Google and GitHub providers',
    acceptance_criteria: [
      'Users can log in with Google',
      'Users can log in with GitHub',
      'JWT tokens are issued on successful login'
    ],
    repo_url: 'https://github.com/example/repo',
    branch: 'feature/auth',
    dependencies: [100, 101],
    required_skills: ['plan', 'design-a-prd', 'tdd'],
    context: 'This is part of the security epic'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockMaestro.getStoryPrompt.mockResolvedValue(samplePrompt);
  });

  it('returns structured prompt', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.success).toBe(true);
    expect(result.prompt).toBeDefined();
    expect(result.prompt?.story_id).toBe(123);
  });

  it('includes title in prompt', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.title).toBe('Implement user authentication');
  });

  it('includes description in prompt', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.description).toContain('OAuth2');
  });

  it('includes acceptance criteria', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.acceptance_criteria).toHaveLength(3);
    expect(result.prompt?.acceptance_criteria).toContain('Users can log in with Google');
  });

  it('includes repo info', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.repo_url).toBe('https://github.com/example/repo');
    expect(result.prompt?.branch).toBe('feature/auth');
  });

  it('includes dependencies', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.dependencies).toEqual([100, 101]);
  });

  it('includes required skills', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.prompt?.required_skills).toContain('plan');
    expect(result.prompt?.required_skills).toContain('tdd');
  });

  it('returns formatted prompt string', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.formatted_prompt).toBeDefined();
    expect(result.formatted_prompt).toContain('# Story 123');
    expect(result.formatted_prompt).toContain('## Acceptance Criteria');
    expect(result.formatted_prompt).toContain('## Repository');
  });

  it('formatted prompt has checkboxes for ACs', async () => {
    const result = await getStoryPrompt({ story_id: 123 });

    expect(result.formatted_prompt).toContain('- [ ] Users can log in with Google');
  });

  it('fails without story_id', async () => {
    const result = await getStoryPrompt({ story_id: 0 });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('handles API errors', async () => {
    mockMaestro.getStoryPrompt.mockRejectedValue(
      new maestroModule.MaestroError('Story not found', 404, false)
    );

    const result = await getStoryPrompt({ story_id: 999 });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Story not found');
  });

  it('handles missing optional fields', async () => {
    mockMaestro.getStoryPrompt.mockResolvedValue({
      story_id: 456,
      title: 'Simple Story',
      description: 'A simple story',
      acceptance_criteria: [],
      dependencies: [],
      required_skills: []
    });

    const result = await getStoryPrompt({ story_id: 456 });

    expect(result.success).toBe(true);
    expect(result.formatted_prompt).not.toContain('## Repository');
    expect(result.formatted_prompt).not.toContain('## Dependencies');
  });
});
