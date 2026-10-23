/**
 * Tests for UI-08: ReworkButton triggers rework flow for failed story
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReworkButton } from '../components/validation/ReworkButton';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useValidation: vi.fn()
}));

describe('ReworkButton - UI-08', () => {
  const mockTriggerRework = vi.fn();
  const mockOnReworkStarted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockTriggerRework.mockResolvedValue(undefined);
  });

  it('renders rework button when validation failed', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} />);
    expect(screen.getByTestId('rework-container')).toBeInTheDocument();
    expect(screen.getByTestId('rework-button')).toBeInTheDocument();
  });

  it('shows rework button text', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} />);
    expect(screen.getByText(/Rework Story/)).toBeInTheDocument();
  });

  it('does not render when validation passed', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'passed',
        timestamp: Date.now(),
        failures: []
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    const { container } = render(<ReworkButton storyId={123} />);
    expect(container.firstChild).toBeNull();
  });

  it('does not render when no result', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: null,
      loading: false,
      triggerRework: mockTriggerRework
    });

    const { container } = render(<ReworkButton storyId={123} />);
    expect(container.firstChild).toBeNull();
  });

  it('calls triggerRework when clicked', async () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} onReworkStarted={mockOnReworkStarted} />);
    fireEvent.click(screen.getByTestId('rework-button'));

    await waitFor(() => {
      expect(mockTriggerRework).toHaveBeenCalled();
    });
  });

  it('calls onReworkStarted callback after success', async () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} onReworkStarted={mockOnReworkStarted} />);
    fireEvent.click(screen.getByTestId('rework-button'));

    await waitFor(() => {
      expect(mockOnReworkStarted).toHaveBeenCalled();
    });
  });

  it('shows loading state while reworking', async () => {
    mockTriggerRework.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} />);
    fireEvent.click(screen.getByTestId('rework-button'));

    expect(screen.getByText('Starting rework...')).toBeInTheDocument();
    expect(screen.getByTestId('rework-button')).toBeDisabled();
  });

  it('shows error when rework fails', async () => {
    mockTriggerRework.mockRejectedValue(new Error('Rework failed'));

    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} />);
    fireEvent.click(screen.getByTestId('rework-button'));

    await waitFor(() => {
      expect(screen.getByTestId('rework-error')).toBeInTheDocument();
      expect(screen.getByText('Rework failed')).toBeInTheDocument();
    });
  });

  it('shows hint text', () => {
    vi.mocked(hooks.useValidation).mockReturnValue({
      result: {
        story_id: 123,
        status: 'failed',
        timestamp: Date.now(),
        failures: ['test failed']
      },
      loading: false,
      triggerRework: mockTriggerRework
    });

    render(<ReworkButton storyId={123} />);
    expect(screen.getByText(/move the story back to In Progress/)).toBeInTheDocument();
  });
});
