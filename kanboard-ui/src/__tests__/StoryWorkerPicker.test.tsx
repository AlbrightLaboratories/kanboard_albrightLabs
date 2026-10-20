/**
 * Tests for UI-13: StoryWorkerPicker allows setting worker labels on story
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { StoryWorkerPicker } from '../components/workers/StoryWorkerPicker';
import * as hooks from '../hooks/useKanboard';
import { kanboardAPI } from '../api/kanboard';

// Mock the hooks and API
vi.mock('../hooks/useKanboard', () => ({
  useWorkers: vi.fn()
}));

vi.mock('../api/kanboard', () => ({
  kanboardAPI: {
    updateWorkerLabels: vi.fn()
  }
}));

describe('StoryWorkerPicker - UI-13', () => {
  const mockOnUpdate = vi.fn();
  const mockStory = {
    id: 123,
    title: 'Test Story',
    description: 'Test',
    column_id: 1,
    project_id: 1,
    owner_id: 0,
    priority: 2,
    position: 1,
    worker_labels: ['python']
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(kanboardAPI.updateWorkerLabels).mockResolvedValue(undefined);
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [
        {
          worker_id: 'ollama-001',
          name: 'Ollama',
          type: 'ollama',
          labels: ['python', 'backend', 'local'],
          capabilities: ['code_generation'],
          status: 'active',
          last_heartbeat: Date.now()
        },
        {
          worker_id: 'vllm-001',
          name: 'vLLM',
          type: 'vllm',
          labels: ['ml', 'gpu-required'],
          capabilities: ['code_generation'],
          status: 'idle',
          last_heartbeat: Date.now()
        }
      ],
      loading: false,
      error: null,
      refresh: vi.fn(),
      registerWorker: vi.fn()
    });
  });

  it('renders story worker picker', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('story-worker-picker')).toBeInTheDocument();
  });

  it('shows Worker Labels header', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByText('Worker Labels')).toBeInTheDocument();
  });

  it('shows currently selected labels', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('selected-labels')).toBeInTheDocument();
    expect(screen.getByText('python ×')).toBeInTheDocument();
  });

  it('shows available labels grid', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('label-grid')).toBeInTheDocument();
  });

  it('shows common labels', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('label-python')).toBeInTheDocument();
    expect(screen.getByTestId('label-typescript')).toBeInTheDocument();
    expect(screen.getByTestId('label-frontend')).toBeInTheDocument();
    expect(screen.getByTestId('label-backend')).toBeInTheDocument();
  });

  it('shows labels from workers', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('label-local')).toBeInTheDocument();
    expect(screen.getByTestId('label-ml')).toBeInTheDocument();
    expect(screen.getByTestId('label-gpu-required')).toBeInTheDocument();
  });

  it('highlights selected labels', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    const pythonButton = screen.getByTestId('label-python');
    expect(pythonButton).toHaveClass('selected');
  });

  it('toggles label on click', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    // Click to add typescript
    fireEvent.click(screen.getByTestId('label-typescript'));
    expect(screen.getByTestId('label-typescript')).toHaveClass('selected');

    // Click again to remove
    fireEvent.click(screen.getByTestId('label-typescript'));
    expect(screen.getByTestId('label-typescript')).not.toHaveClass('selected');
  });

  it('removes label when clicking selected label', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    // Click the selected label to remove it
    fireEvent.click(screen.getByText('python ×'));

    // Should no longer be in selected labels
    expect(screen.queryByText('python ×')).not.toBeInTheDocument();
  });

  it('shows custom label input', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('custom-label-input')).toBeInTheDocument();
  });

  it('adds custom label', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    const input = screen.getByTestId('custom-label-input');
    fireEvent.change(input, { target: { value: 'my-custom-label' } });
    fireEvent.click(screen.getByTestId('add-label-button'));

    expect(screen.getByText('my-custom-label ×')).toBeInTheDocument();
  });

  it('adds custom label on Enter key', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    const input = screen.getByTestId('custom-label-input');
    fireEvent.change(input, { target: { value: 'enter-label' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(screen.getByText('enter-label ×')).toBeInTheDocument();
  });

  it('clears input after adding custom label', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    const input = screen.getByTestId('custom-label-input');
    fireEvent.change(input, { target: { value: 'custom' } });
    fireEvent.click(screen.getByTestId('add-label-button'));

    expect(input).toHaveValue('');
  });

  it('shows matching workers when labels selected', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByTestId('matching-workers')).toBeInTheDocument();
    expect(screen.getByText(/Matching Workers/)).toBeInTheDocument();
  });

  it('shows worker count', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    // Python matches ollama-001
    expect(screen.getByText(/Matching Workers \(1\)/)).toBeInTheDocument();
  });

  it('shows worker names in matching list', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.getByText('Ollama (ollama)')).toBeInTheDocument();
  });

  it('shows no labels message when empty', () => {
    const storyNoLabels = { ...mockStory, worker_labels: [] };
    render(<StoryWorkerPicker story={storyNoLabels} />);
    expect(screen.getByText(/No labels selected/)).toBeInTheDocument();
  });

  it('shows Save button when labels changed', () => {
    render(<StoryWorkerPicker story={mockStory} />);

    // Change labels
    fireEvent.click(screen.getByTestId('label-typescript'));

    expect(screen.getByTestId('save-labels-button')).toBeInTheDocument();
  });

  it('hides Save button when no changes', () => {
    render(<StoryWorkerPicker story={mockStory} />);
    expect(screen.queryByTestId('save-labels-button')).not.toBeInTheDocument();
  });

  it('saves labels when Save clicked', async () => {
    render(<StoryWorkerPicker story={mockStory} onUpdate={mockOnUpdate} />);

    // Add a label
    fireEvent.click(screen.getByTestId('label-typescript'));

    // Save
    fireEvent.click(screen.getByTestId('save-labels-button'));

    await waitFor(() => {
      expect(kanboardAPI.updateWorkerLabels).toHaveBeenCalledWith(
        123,
        ['python', 'typescript']
      );
    });
  });

  it('calls onUpdate after saving', async () => {
    render(<StoryWorkerPicker story={mockStory} onUpdate={mockOnUpdate} />);

    fireEvent.click(screen.getByTestId('label-typescript'));
    fireEvent.click(screen.getByTestId('save-labels-button'));

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalledWith(['python', 'typescript']);
    });
  });

  it('shows saving state', async () => {
    vi.mocked(kanboardAPI.updateWorkerLabels).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<StoryWorkerPicker story={mockStory} />);

    fireEvent.click(screen.getByTestId('label-typescript'));
    fireEvent.click(screen.getByTestId('save-labels-button'));

    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('disables Save button while saving', async () => {
    vi.mocked(kanboardAPI.updateWorkerLabels).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<StoryWorkerPicker story={mockStory} />);

    fireEvent.click(screen.getByTestId('label-typescript'));
    fireEvent.click(screen.getByTestId('save-labels-button'));

    expect(screen.getByTestId('save-labels-button')).toBeDisabled();
  });
});
