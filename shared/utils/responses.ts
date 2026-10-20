/**
 * Standardized Response Types
 * Unified response envelope for all modules
 *
 * Addresses output-style inconsistencies:
 * - Unified error codes
 * - Consistent field naming (failure_reasons, not failure_reason)
 * - Retryability flags
 * - Request tracing
 */

// Error codes - semantic, not HTTP status
export type ErrorCode =
  | 'NOT_FOUND'           // Resource doesn't exist
  | 'UNAUTHORIZED'        // Auth failed
  | 'FORBIDDEN'           // Permission denied
  | 'TIMEOUT'             // Operation timed out (retryable)
  | 'RATE_LIMITED'        // Too many requests (retryable)
  | 'CONFLICT'            // Resource conflict (e.g., already claimed)
  | 'VALIDATION_FAILED'   // Input validation failed
  | 'INTERNAL_ERROR'      // Server error (retryable)
  | 'SERVICE_UNAVAILABLE' // Dependency down (retryable)
  | 'ALREADY_EXISTS'      // Duplicate creation
  | 'SKILL_FAILED'        // Skill execution failed
  | 'VALIDATION_FAILED_AC'; // Acceptance criteria not met

// Error detail structure
export interface ErrorDetail {
  code: ErrorCode;
  message: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}

// Standard response envelope
export interface StandardResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ErrorDetail;
  timestamp: number;
  request_id?: string;
}

// Helper to create success response
export function successResponse<T>(
  data: T,
  requestId?: string
): StandardResponse<T> {
  return {
    success: true,
    data,
    timestamp: Date.now(),
    request_id: requestId,
  };
}

// Helper to create error response
export function errorResponse(
  code: ErrorCode,
  message: string,
  retryable: boolean = false,
  details?: Record<string, unknown>,
  requestId?: string
): StandardResponse<never> {
  return {
    success: false,
    error: {
      code,
      message,
      retryable,
      details,
    },
    timestamp: Date.now(),
    request_id: requestId,
  };
}

// Retryable error codes
export const RETRYABLE_ERRORS: Set<ErrorCode> = new Set([
  'TIMEOUT',
  'RATE_LIMITED',
  'INTERNAL_ERROR',
  'SERVICE_UNAVAILABLE',
]);

// Check if error is retryable
export function isRetryable(error: ErrorDetail): boolean {
  return error.retryable || RETRYABLE_ERRORS.has(error.code);
}

// Status enum - consistent across all modules
export type Status = 'pending' | 'in_progress' | 'passed' | 'failed';

// Validation result with consistent field names
export interface ValidationResult {
  status: 'passed' | 'failed';
  timestamp: string;
  message: string;
  failure_reasons: string[]; // Always plural for consistency
  coverage?: number;
  test_count?: number;
  passed_count?: number;
}

// Skill execution result with consistent field names
export interface SkillResult {
  status: Status;
  output?: Record<string, unknown>;
  failure_reasons: string[]; // Always plural for consistency
  started_at?: string;
  completed_at?: string;
  agent_id?: string;
}

// Structured logging helper
export interface LogContext {
  action: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  timestamp: number;
  request_id?: string;
  [key: string]: unknown;
}

export function structuredLog(ctx: Omit<LogContext, 'timestamp'>): void {
  const log: LogContext = {
    ...ctx,
    timestamp: Date.now(),
  };
  console.error(JSON.stringify(log));
}

// MCP Tool result type - standardized
export interface MCPToolResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: ErrorCode;
    message: string;
    retryable: boolean;
  };
  timestamp: number;
  request_id?: string;
}

// Helper for MCP tools
export function mcpSuccess<T>(data: T, requestId?: string): MCPToolResult<T> {
  return {
    success: true,
    data,
    timestamp: Date.now(),
    request_id: requestId,
  };
}

export function mcpError(
  code: ErrorCode,
  message: string,
  retryable: boolean = false,
  requestId?: string
): MCPToolResult<never> {
  return {
    success: false,
    error: { code, message, retryable },
    timestamp: Date.now(),
    request_id: requestId,
  };
}
