/**
 * Test MCP-05: kanboard_execute_skill triggers skill and returns execution ID
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { executeSkill } from '../tools/skill/executeSkill.js';
import * as maestroModule from '../clients/maestroClient.js';

// Mock the Maestro client
vi.mock('../clients/maestroClient.js', () => ({
  maestroClient: {
    executeSkill: vi.fn()
  },
  MaestroError: class MaestroError extends Error {
    constructor(message: string, public statusCode?: number, public retryable: boolean = false) {
      super(message);
      this.name = 'MaestroError';
    }
  }
}));

describe('kanboard_execute_skill', () => {
  const mockMaestro = maestroModule.maestroClient as {
    executeSkill: Mock;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockMaestro.executeSkill.mockResolvedValue({
      execution_id: 'exec-123-abc',
      skill_name: 'tdd',
      story_id: 123,
      status: 'running'
    });
  });

  it('executes skill and returns execution ID', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'tdd'
    });

    expect(result.success).toBe(true);
    expect(result.execution_id).toBe('exec-123-abc');
    expect(result.skill_name).toBe('tdd');
  });

  it('returns execution status', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'plan'
    });

    expect(result.status).toBe('running');
  });

  it('executes plan skill', async () => {
    await executeSkill({
      story_id: 123,
      skill_name: 'plan'
    });

    expect(mockMaestro.executeSkill).toHaveBeenCalledWith(
      123,
      'plan',
      undefined
    );
  });

  it('executes design-a-prd skill', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'design-a-prd'
    });

    expect(result.success).toBe(true);
  });

  it('executes tdd skill', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'tdd'
    });

    expect(result.success).toBe(true);
  });

  it('executes prove-it skill', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'prove-it'
    });

    expect(result.success).toBe(true);
  });

  it('executes release-it skill', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'release-it'
    });

    expect(result.success).toBe(true);
  });

  it('fails for invalid skill name', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'invalid-skill'
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('Invalid skill');
    expect(result.error).toContain('plan');
  });

  it('fails without story_id', async () => {
    const result = await executeSkill({
      story_id: 0,
      skill_name: 'tdd'
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('fails without skill_name', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: ''
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('required');
  });

  it('passes optional params to skill', async () => {
    const params = { coverage_threshold: 80 };

    await executeSkill({
      story_id: 123,
      skill_name: 'tdd',
      params
    });

    expect(mockMaestro.executeSkill).toHaveBeenCalledWith(
      123,
      'tdd',
      params
    );
  });

  it('handles API errors', async () => {
    mockMaestro.executeSkill.mockRejectedValue(
      new maestroModule.MaestroError('Skill execution failed', 500, true)
    );

    const result = await executeSkill({
      story_id: 123,
      skill_name: 'tdd'
    });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Skill execution failed');
  });

  it('lists valid skills in error message', async () => {
    const result = await executeSkill({
      story_id: 123,
      skill_name: 'bad'
    });

    expect(result.error).toContain('plan');
    expect(result.error).toContain('design-a-prd');
    expect(result.error).toContain('tdd');
    expect(result.error).toContain('prove-it');
    expect(result.error).toContain('release-it');
  });
});
