/**
 * Tests for Standardized Response Types - SH-03, SH-04, SH-05
 *
 * SH-03: Standardized response types unify error handling
 * SH-04: Error codes are semantic and include retryable flag
 * SH-05: Structured logging helper outputs JSON to stderr
 */

import { vi, describe, it, expect, beforeEach, afterEach, SpyInstance } from 'vitest';
import {
  ErrorCode,
  ErrorDetail,
  StandardResponse,
  successResponse,
  errorResponse,
  RETRYABLE_ERRORS,
  isRetryable,
  ValidationResult,
  SkillResult,
  structuredLog,
  mcpSuccess,
  mcpError,
  MCPToolResult,
} from '../utils/responses';

describe('SH-03: Standardized response types unify error handling', () => {
  describe('successResponse helper', () => {
    it('creates success response with data', () => {
      const data = { id: '123', name: 'Test' };
      const response = successResponse(data);

      expect(response.success).toBe(true);
      expect(response.data).toEqual(data);
      expect(response.timestamp).toBeDefined();
      expect(response.error).toBeUndefined();
    });

    it('includes request_id when provided', () => {
      const response = successResponse({ test: true }, 'req-123');

      expect(response.request_id).toBe('req-123');
    });

    it('has consistent timestamp format', () => {
      const response = successResponse({});

      expect(typeof response.timestamp).toBe('number');
      expect(response.timestamp).toBeGreaterThan(0);
    });
  });

  describe('errorResponse helper', () => {
    it('creates error response with code and message', () => {
      const response = errorResponse('NOT_FOUND', 'Story not found');

      expect(response.success).toBe(false);
      expect(response.error?.code).toBe('NOT_FOUND');
      expect(response.error?.message).toBe('Story not found');
      expect(response.data).toBeUndefined();
    });

    it('includes retryable flag', () => {
      const nonRetryable = errorResponse('NOT_FOUND', 'Not found', false);
      const retryable = errorResponse('TIMEOUT', 'Timed out', true);

      expect(nonRetryable.error?.retryable).toBe(false);
      expect(retryable.error?.retryable).toBe(true);
    });

    it('includes details when provided', () => {
      const response = errorResponse(
        'VALIDATION_FAILED',
        'Invalid input',
        false,
        { field: 'title', reason: 'required' }
      );

      expect(response.error?.details).toEqual({
        field: 'title',
        reason: 'required',
      });
    });
  });

  describe('ValidationResult consistency', () => {
    it('uses failure_reasons (plural) not failure_reason', () => {
      const result: ValidationResult = {
        status: 'failed',
        timestamp: new Date().toISOString(),
        message: 'Tests failed',
        failure_reasons: ['Test A failed', 'Test B failed'],
        test_count: 10,
        passed_count: 8,
      };

      expect(result.failure_reasons).toHaveLength(2);
      // @ts-expect-error - verify no singular version
      expect(result.failure_reason).toBeUndefined();
    });
  });

  describe('SkillResult consistency', () => {
    it('uses failure_reasons (plural) for consistency', () => {
      const result: SkillResult = {
        status: 'failed',
        failure_reasons: ['TDD tests not passing', 'Coverage below 80%'],
      };

      expect(result.failure_reasons).toHaveLength(2);
    });

    it('supports all status values', () => {
      const statuses: SkillResult['status'][] = [
        'pending',
        'in_progress',
        'passed',
        'failed',
      ];

      statuses.forEach(status => {
        const result: SkillResult = {
          status,
          failure_reasons: [],
        };
        expect(result.status).toBe(status);
      });
    });
  });

  describe('MCP Tool result types', () => {
    it('mcpSuccess creates success result', () => {
      const result = mcpSuccess({ tools: ['git', 'kubectl'] }, 'req-1');

      expect(result.success).toBe(true);
      expect(result.data?.tools).toContain('git');
      expect(result.request_id).toBe('req-1');
    });

    it('mcpError creates error result', () => {
      const result = mcpError('TIMEOUT', 'Tool timed out', true, 'req-2');

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('TIMEOUT');
      expect(result.error?.retryable).toBe(true);
    });
  });
});

describe('SH-04: Error codes are semantic and include retryable flag', () => {
  describe('Error codes are semantic', () => {
    const errorCodes: ErrorCode[] = [
      'NOT_FOUND',
      'UNAUTHORIZED',
      'FORBIDDEN',
      'TIMEOUT',
      'RATE_LIMITED',
      'CONFLICT',
      'VALIDATION_FAILED',
      'INTERNAL_ERROR',
      'SERVICE_UNAVAILABLE',
      'ALREADY_EXISTS',
      'SKILL_FAILED',
      'VALIDATION_FAILED_AC',
    ];

    it('all error codes are defined', () => {
      expect(errorCodes).toHaveLength(12);
    });

    it.each(errorCodes)('error code %s is a semantic string', (code) => {
      // All codes are SCREAMING_SNAKE_CASE
      expect(code).toMatch(/^[A-Z_]+$/);
      // Not HTTP status codes
      expect(parseInt(code)).toBeNaN();
    });
  });

  describe('Retryable errors are correctly identified', () => {
    it('RETRYABLE_ERRORS set contains timeout-related codes', () => {
      expect(RETRYABLE_ERRORS.has('TIMEOUT')).toBe(true);
      expect(RETRYABLE_ERRORS.has('RATE_LIMITED')).toBe(true);
      expect(RETRYABLE_ERRORS.has('INTERNAL_ERROR')).toBe(true);
      expect(RETRYABLE_ERRORS.has('SERVICE_UNAVAILABLE')).toBe(true);
    });

    it('RETRYABLE_ERRORS does not contain permanent errors', () => {
      expect(RETRYABLE_ERRORS.has('NOT_FOUND')).toBe(false);
      expect(RETRYABLE_ERRORS.has('UNAUTHORIZED')).toBe(false);
      expect(RETRYABLE_ERRORS.has('FORBIDDEN')).toBe(false);
      expect(RETRYABLE_ERRORS.has('VALIDATION_FAILED')).toBe(false);
    });
  });

  describe('isRetryable helper', () => {
    it('returns true for retryable error codes', () => {
      const error: ErrorDetail = {
        code: 'TIMEOUT',
        message: 'Request timed out',
        retryable: true,
      };

      expect(isRetryable(error)).toBe(true);
    });

    it('returns true when error.retryable is true even if code not in set', () => {
      const error: ErrorDetail = {
        code: 'NOT_FOUND',
        message: 'Temporarily not found',
        retryable: true, // Explicitly marked retryable
      };

      expect(isRetryable(error)).toBe(true);
    });

    it('returns true for errors in RETRYABLE_ERRORS set', () => {
      const error: ErrorDetail = {
        code: 'SERVICE_UNAVAILABLE',
        message: 'Service down',
        retryable: false, // Even if marked false, code is in set
      };

      expect(isRetryable(error)).toBe(true);
    });

    it('returns false for non-retryable errors', () => {
      const error: ErrorDetail = {
        code: 'NOT_FOUND',
        message: 'Story does not exist',
        retryable: false,
      };

      expect(isRetryable(error)).toBe(false);
    });
  });

  describe('ErrorDetail structure', () => {
    it('includes all required fields', () => {
      const error: ErrorDetail = {
        code: 'CONFLICT',
        message: 'Story already claimed',
        retryable: false,
        details: { claimed_by: 'agent-1' },
      };

      expect(error.code).toBeDefined();
      expect(error.message).toBeDefined();
      expect(typeof error.retryable).toBe('boolean');
    });
  });
});

describe('SH-05: Structured logging helper outputs JSON to stderr', () => {
  let consoleErrorSpy: SpyInstance;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('outputs JSON to stderr via console.error', () => {
    structuredLog({
      action: 'story_moved',
      level: 'INFO',
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    const output = consoleErrorSpy.mock.calls[0][0];
    expect(typeof output).toBe('string');

    // Should be valid JSON
    const parsed = JSON.parse(output);
    expect(parsed.action).toBe('story_moved');
  });

  it('includes timestamp automatically', () => {
    structuredLog({
      action: 'test_action',
      level: 'DEBUG',
    });

    const output = JSON.parse(consoleErrorSpy.mock.calls[0][0]);
    expect(output.timestamp).toBeDefined();
    expect(typeof output.timestamp).toBe('number');
  });

  it('supports all log levels', () => {
    const levels: Array<'DEBUG' | 'INFO' | 'WARN' | 'ERROR'> = [
      'DEBUG',
      'INFO',
      'WARN',
      'ERROR',
    ];

    levels.forEach(level => {
      structuredLog({ action: 'test', level });
    });

    expect(consoleErrorSpy).toHaveBeenCalledTimes(4);
  });

  it('includes request_id when provided', () => {
    structuredLog({
      action: 'api_call',
      level: 'INFO',
      request_id: 'req-abc-123',
    });

    const output = JSON.parse(consoleErrorSpy.mock.calls[0][0]);
    expect(output.request_id).toBe('req-abc-123');
  });

  it('supports custom fields', () => {
    structuredLog({
      action: 'story_created',
      level: 'INFO',
      story_id: 'story-123',
      project: 'kanboard',
      user: 'hermes',
    });

    const output = JSON.parse(consoleErrorSpy.mock.calls[0][0]);
    expect(output.story_id).toBe('story-123');
    expect(output.project).toBe('kanboard');
    expect(output.user).toBe('hermes');
  });

  it('outputs valid JSON that can be piped to log aggregators', () => {
    structuredLog({
      action: 'skill_completed',
      level: 'INFO',
      skill: 'tdd',
      status: 'passed',
      duration_ms: 1500,
    });

    const output = consoleErrorSpy.mock.calls[0][0];

    // Should be valid JSON without trailing newline issues
    expect(() => JSON.parse(output)).not.toThrow();

    // Common log aggregator expectations
    const parsed = JSON.parse(output);
    expect(parsed).toHaveProperty('timestamp');
    expect(parsed).toHaveProperty('level');
    expect(parsed).toHaveProperty('action');
  });
});
