/**
 * Tests for UI-14: WorkerAssignment shows current worker and allows reassignment
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkerAssignment } from '../components/workers/WorkerAssignment';
import * as hooks from '../hooks/useKanboard';
import { kanboardAPI } from '../api/kanboard';

// Mock the hooks and API
vi.mock('../hooks/useKanboard', () => ({
  useWorkers: vi.fn()
}));

vi.mock('../api/kanboard', () => ({
  kanboardAPI: {
    assignWorker: vi.fn()
  }
}));

describe('WorkerAssignment - UI-14', () => {
  const mockOnAssigned = vi.fn();
  const mockStory = {
    id: 123,
    title: 'Test Story',
    description: 'Test',
    column_id: 1,
    project_id: 1,
    owner_id: 0,
    priority: 2,
    position: 1,
    worker_labels: ['python', 'backend'],
    assigned_worker: 'ollama-001'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(kanboardAPI.assignWorker).mockResolvedValue(undefined);
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [
        {
          worker_id: 'ollama-001',
          name: 'Ollama-Llama3',
          type: 'ollama',
          labels: ['python', 'backend'],
          capabilities: ['code_generation'],
          status: 'active',
          last_heartbeat: Date.now()
        },
        {
          worker_id: 'vllm-001',
          name: 'vLLM-70B',
          type: 'vllm',
          labels: ['python', 'ml'],
          capabilities: ['code_generation'],
          status: 'idle',
          last_heartbeat: Date.now()
        },
        {
          worker_id: 'claude-001',
          name: 'Claude-Code',
          type: 'claude',
          labels: ['typescript', 'frontend'],
          capabilities: ['code_generation'],
          status: 'active',
          last_heartbeat: Date.now()
        },
        {
          worker_id: 'offline-001',
          name: 'Offline Worker',
          type: 'custom',
          labels: ['python'],
          capabilities: ['code_generation'],
          status: 'offline',
          last_heartbeat: Date.now() - 300000
        }
      ],
      loading: false,
      error: null,
      refresh: vi.fn(),
      registerWorker: vi.fn()
    });
  });

  it('renders worker assignment', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByTestId('worker-assignment')).toBeInTheDocument();
  });

  it('shows Assigned Worker header', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByText('Assigned Worker')).toBeInTheDocument();
  });

  it('shows current worker when assigned', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByTestId('current-worker')).toBeInTheDocument();
    expect(screen.getByText('Ollama-Llama3')).toBeInTheDocument();
  });

  it('shows worker type', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByText('(ollama)')).toBeInTheDocument();
  });

  it('shows worker status badge', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('shows Reassign button when worker assigned', () => {
    render(<WorkerAssignment story={mockStory} />);
    expect(screen.getByTestId('reassign-button')).toBeInTheDocument();
    expect(screen.getByText('Reassign')).toBeInTheDocument();
  });

  it('shows no worker message when not assigned', () => {
    const unassignedStory = { ...mockStory, assigned_worker: undefined };
    render(<WorkerAssignment story={unassignedStory} />);
    expect(screen.getByTestId('no-worker')).toBeInTheDocument();
    expect(screen.getByText('No worker assigned')).toBeInTheDocument();
  });

  it('shows Assign Worker button when not assigned', () => {
    const unassignedStory = { ...mockStory, assigned_worker: undefined };
    render(<WorkerAssignment story={unassignedStory} />);
    expect(screen.getByTestId('assign-button')).toBeInTheDocument();
  });

  it('opens picker when Reassign clicked', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    expect(screen.getByTestId('worker-picker')).toBeInTheDocument();
  });

  it('opens picker when Assign clicked', () => {
    const unassignedStory = { ...mockStory, assigned_worker: undefined };
    render(<WorkerAssignment story={unassignedStory} />);
    fireEvent.click(screen.getByTestId('assign-button'));
    expect(screen.getByTestId('worker-picker')).toBeInTheDocument();
  });

  it('shows Select Worker header in picker', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    expect(screen.getByText('Select Worker')).toBeInTheDocument();
  });

  it('shows close button in picker', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    expect(screen.getByText('×')).toBeInTheDocument();
  });

  it('closes picker when close clicked', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByText('×'));
    expect(screen.queryByTestId('worker-picker')).not.toBeInTheDocument();
  });

  it('shows workers matching story labels', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    // Should show ollama-001 and vllm-001 (both have python or backend label)
    expect(screen.getByTestId('worker-option-ollama-001')).toBeInTheDocument();
    expect(screen.getByTestId('worker-option-vllm-001')).toBeInTheDocument();
  });

  it('excludes offline workers', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    // offline-001 has python label but is offline
    expect(screen.queryByTestId('worker-option-offline-001')).not.toBeInTheDocument();
  });

  it('excludes workers without matching labels', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    // claude-001 has typescript/frontend, not python/backend
    expect(screen.queryByTestId('worker-option-claude-001')).not.toBeInTheDocument();
  });

  it('shows no workers message when none match', () => {
    const storyNoMatch = { ...mockStory, worker_labels: ['nonexistent-label'] };
    render(<WorkerAssignment story={storyNoMatch} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    expect(screen.getByText(/No workers available/)).toBeInTheDocument();
  });

  it('assigns worker when option clicked', async () => {
    render(<WorkerAssignment story={mockStory} onAssigned={mockOnAssigned} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByTestId('worker-option-vllm-001'));

    await waitFor(() => {
      expect(kanboardAPI.assignWorker).toHaveBeenCalledWith(123, 'vllm-001');
    });
  });

  it('calls onAssigned after successful assignment', async () => {
    render(<WorkerAssignment story={mockStory} onAssigned={mockOnAssigned} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByTestId('worker-option-vllm-001'));

    await waitFor(() => {
      expect(mockOnAssigned).toHaveBeenCalledWith('vllm-001');
    });
  });

  it('closes picker after assignment', async () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByTestId('worker-option-vllm-001'));

    await waitFor(() => {
      expect(screen.queryByTestId('worker-picker')).not.toBeInTheDocument();
    });
  });

  it('shows error on assignment failure', async () => {
    vi.mocked(kanboardAPI.assignWorker).mockRejectedValue(new Error('Assignment failed'));

    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByTestId('worker-option-vllm-001'));

    await waitFor(() => {
      expect(screen.getByTestId('assignment-error')).toBeInTheDocument();
      expect(screen.getByText('Assignment failed')).toBeInTheDocument();
    });
  });

  it('shows assigning indicator', async () => {
    vi.mocked(kanboardAPI.assignWorker).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));
    fireEvent.click(screen.getByTestId('worker-option-vllm-001'));

    expect(screen.getByText('Assigning...')).toBeInTheDocument();
  });

  it('shows worker labels in picker', () => {
    render(<WorkerAssignment story={mockStory} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    // vllm-001 has python label
    const vllmOption = screen.getByTestId('worker-option-vllm-001');
    expect(vllmOption).toContainHTML('python');
  });

  it('shows all workers when no story labels', () => {
    const storyNoLabels = { ...mockStory, worker_labels: [] };
    render(<WorkerAssignment story={storyNoLabels} />);
    fireEvent.click(screen.getByTestId('reassign-button'));

    // Should show all non-offline workers
    expect(screen.getByTestId('worker-option-ollama-001')).toBeInTheDocument();
    expect(screen.getByTestId('worker-option-vllm-001')).toBeInTheDocument();
    expect(screen.getByTestId('worker-option-claude-001')).toBeInTheDocument();
  });
});
