/**
 * Tests for UI-07: ValidationResult shows pass/fail with failure log
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ValidationResult } from '../components/validation/ValidationResult';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useValidation: vi.fn()
}));

describe('ValidationResult - UI-07', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders validation result', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp: Date.now(),
        failures: []
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByTestId('validation-result')).toBeInTheDocument();
  });

  it('shows passed status', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp: Date.now(),
        failures: []
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText('Validation Passed')).toBeInTheDocument();
    expect(screen.getByTestId('validation-result')).toHaveClass('passed');
  });

  it('shows failed status', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['Test 1 failed']
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText('Validation Failed')).toBeInTheDocument();
    expect(screen.getByTestId('validation-result')).toHaveClass('failed');
  });

  it('shows pass icon for passed validation', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp: Date.now(),
        failures: []
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('shows fail icon for failed validation', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['Test failed']
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText('✗')).toBeInTheDocument();
  });

  it('shows failure log when failed', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test_login failed', 'coverage below 80%']
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByTestId('failure-log')).toBeInTheDocument();
    expect(screen.getByText('test_login failed')).toBeInTheDocument();
    expect(screen.getByText('coverage below 80%')).toBeInTheDocument();
  });

  it('shows failure count', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['error 1', 'error 2', 'error 3']
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText('Failures (3)')).toBeInTheDocument();
  });

  it('hides failure log when passed', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp: Date.now(),
        failures: []
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.queryByTestId('failure-log')).not.toBeInTheDocument();
  });

  it('shows timestamp', () => {
    const timestamp = Date.now();
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp,
        failures: []
      },
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText(/Ran:/)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: null,
      loading: true,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows pending state when no result', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: null,
      loading: false,
      triggerRework: vi.fn()
    });

    render(<ValidationResult storyId={123} />);
    expect(screen.getByTestId('validation-pending')).toBeInTheDocument();
    expect(screen.getByText('Validation not yet run')).toBeInTheDocument();
  });
});
