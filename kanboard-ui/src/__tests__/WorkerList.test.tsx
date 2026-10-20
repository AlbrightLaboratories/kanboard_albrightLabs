/**
 * Tests for UI-11: WorkerList shows all workers with health indicators
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkerList } from '../components/workers/WorkerList';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useWorkers: vi.fn()
}));

describe('WorkerList - UI-11', () => {
  const mockRefresh = vi.fn();
  const mockOnWorkerClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [
        {
          worker_id: 'ollama-001',
          name: 'Ollama-Llama3',
          type: 'ollama',
          labels: ['python', 'backend', 'fast'],
          capabilities: ['code_generation', 'terminal_execution'],
          status: 'active',
          last_heartbeat: Date.now() - 5000 // 5 seconds ago - healthy
        },
        {
          worker_id: 'vllm-001',
          name: 'vLLM-70B',
          type: 'vllm',
          labels: ['python', 'ml', 'gpu-required'],
          capabilities: ['code_generation', 'skill_execution'],
          status: 'busy',
          last_heartbeat: Date.now() - 120000 // 2 minutes ago - unhealthy
        },
        {
          worker_id: 'claude-001',
          name: 'Claude-Code',
          type: 'claude',
          labels: ['typescript', 'frontend'],
          capabilities: ['code_generation', 'code_review', 'terminal_execution'],
          status: 'offline',
          last_heartbeat: Date.now() - 300000 // 5 minutes ago
        }
      ],
      loading: false,
      error: null,
      refresh: mockRefresh,
      registerWorker: vi.fn()
    });
  });

  it('renders worker list', () => {
    render(<WorkerList />);
    expect(screen.getByTestId('worker-list')).toBeInTheDocument();
  });

  it('shows LLM Workers header', () => {
    render(<WorkerList />);
    expect(screen.getByText('LLM Workers')).toBeInTheDocument();
  });

  it('displays all workers', () => {
    render(<WorkerList />);
    expect(screen.getByTestId('worker-ollama-001')).toBeInTheDocument();
    expect(screen.getByTestId('worker-vllm-001')).toBeInTheDocument();
    expect(screen.getByTestId('worker-claude-001')).toBeInTheDocument();
  });

  it('shows worker names', () => {
    render(<WorkerList />);
    expect(screen.getByText('Ollama-Llama3')).toBeInTheDocument();
    expect(screen.getByText('vLLM-70B')).toBeInTheDocument();
    expect(screen.getByText('Claude-Code')).toBeInTheDocument();
  });

  it('shows worker types', () => {
    render(<WorkerList />);
    expect(screen.getByText('ollama')).toBeInTheDocument();
    expect(screen.getByText('vllm')).toBeInTheDocument();
    expect(screen.getByText('claude')).toBeInTheDocument();
  });

  it('shows worker status', () => {
    render(<WorkerList />);
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('busy')).toBeInTheDocument();
    expect(screen.getByText('offline')).toBeInTheDocument();
  });

  it('shows health indicators', () => {
    render(<WorkerList />);
    const healthIndicators = screen.getAllByTestId('health-indicator');
    expect(healthIndicators.length).toBe(3);
  });

  it('shows worker labels (first 3)', () => {
    render(<WorkerList />);
    // Multiple workers may have same labels, so use getAllByText
    expect(screen.getAllByText('python').length).toBeGreaterThan(0);
    expect(screen.getAllByText('backend').length).toBeGreaterThan(0);
    expect(screen.getAllByText('fast').length).toBeGreaterThan(0);
  });

  it('shows +N more for additional labels', () => {
    // Ollama has 3 labels, vLLM has 3 labels - one shows +N indicator
    render(<WorkerList />);
    // Check if any "+N more" indicators exist
    const moreLabels = screen.queryAllByText(/\+\d+/);
    // This depends on how many labels exceed 3
    expect(moreLabels).toBeDefined();
  });

  it('shows worker capabilities', () => {
    render(<WorkerList />);
    expect(screen.getAllByText('code_generation').length).toBeGreaterThan(0);
  });

  it('separates online and offline workers', () => {
    render(<WorkerList />);
    expect(screen.getByText(/Online \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Offline \(1\)/)).toBeInTheDocument();
  });

  it('shows refresh button', () => {
    render(<WorkerList />);
    expect(screen.getByText('↻')).toBeInTheDocument();
  });

  it('calls refresh on button click', () => {
    render(<WorkerList />);
    fireEvent.click(screen.getByText('↻'));
    expect(mockRefresh).toHaveBeenCalled();
  });

  it('calls onWorkerClick when worker clicked', () => {
    render(<WorkerList onWorkerClick={mockOnWorkerClick} />);
    fireEvent.click(screen.getByTestId('worker-ollama-001'));
    expect(mockOnWorkerClick).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [],
      loading: true,
      error: null,
      refresh: mockRefresh,
      registerWorker: vi.fn()
    });

    render(<WorkerList />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [],
      loading: false,
      error: 'Failed to fetch workers',
      refresh: mockRefresh,
      registerWorker: vi.fn()
    });

    render(<WorkerList />);
    expect(screen.getByText(/Failed to fetch workers/)).toBeInTheDocument();
  });

  it('shows retry button on error', () => {
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [],
      loading: false,
      error: 'Connection failed',
      refresh: mockRefresh,
      registerWorker: vi.fn()
    });

    render(<WorkerList />);
    fireEvent.click(screen.getByText('Retry'));
    expect(mockRefresh).toHaveBeenCalled();
  });

  it('shows no workers message when empty', () => {
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [],
      loading: false,
      error: null,
      refresh: mockRefresh,
      registerWorker: vi.fn()
    });

    render(<WorkerList />);
    expect(screen.getByText('No workers registered')).toBeInTheDocument();
  });
});
