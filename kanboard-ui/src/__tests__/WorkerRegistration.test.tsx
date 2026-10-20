/**
 * Tests for UI-12: WorkerRegistration form validates and submits new worker
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkerRegistration } from '../components/workers/WorkerRegistration';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useWorkers: vi.fn()
}));

describe('WorkerRegistration - UI-12', () => {
  const mockRegisterWorker = vi.fn();
  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockRegisterWorker.mockResolvedValue(undefined);
    vi.mocked(hooks.useWorkers).mockReturnValue({
      workers: [],
      loading: false,
      error: null,
      refresh: vi.fn(),
      registerWorker: mockRegisterWorker
    });
  });

  it('renders registration form', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('worker-registration')).toBeInTheDocument();
  });

  it('shows form title', () => {
    render(<WorkerRegistration />);
    expect(screen.getByText('Register New Worker')).toBeInTheDocument();
  });

  it('shows name input', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('name-input')).toBeInTheDocument();
    expect(screen.getByLabelText(/Name/)).toBeInTheDocument();
  });

  it('shows type select', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('type-select')).toBeInTheDocument();
  });

  it('shows all worker types', () => {
    render(<WorkerRegistration />);
    const select = screen.getByTestId('type-select');
    expect(select).toContainHTML('claude');
    expect(select).toContainHTML('gemini');
    expect(select).toContainHTML('codex');
    expect(select).toContainHTML('ollama');
    expect(select).toContainHTML('vllm');
    expect(select).toContainHTML('custom');
  });

  it('shows labels input', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('labels-input')).toBeInTheDocument();
  });

  it('shows capabilities checkboxes', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('capabilities')).toBeInTheDocument();
    expect(screen.getByTestId('cap-code_generation')).toBeInTheDocument();
    expect(screen.getByTestId('cap-terminal_execution')).toBeInTheDocument();
  });

  it('shows submit button', () => {
    render(<WorkerRegistration />);
    expect(screen.getByTestId('submit-button')).toBeInTheDocument();
    expect(screen.getByText('Register Worker')).toBeInTheDocument();
  });

  it('validates required name', async () => {
    render(<WorkerRegistration />);
    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });
    expect(mockRegisterWorker).not.toHaveBeenCalled();
  });

  it('validates at least one capability', async () => {
    render(<WorkerRegistration />);

    // Fill name
    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    // Uncheck the default capability
    fireEvent.click(screen.getByTestId('cap-code_generation'));

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByText('At least one capability is required')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    render(<WorkerRegistration onSuccess={mockOnSuccess} />);

    // Fill name
    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'My Ollama Worker' }
    });

    // Select type
    fireEvent.change(screen.getByTestId('type-select'), {
      target: { value: 'ollama' }
    });

    // Add labels
    fireEvent.change(screen.getByTestId('labels-input'), {
      target: { value: 'python, backend' }
    });

    // Add capability
    fireEvent.click(screen.getByTestId('cap-terminal_execution'));

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockRegisterWorker).toHaveBeenCalledWith({
        name: 'My Ollama Worker',
        type: 'ollama',
        labels: ['python', 'backend'],
        capabilities: ['code_generation', 'terminal_execution']
      });
    });
  });

  it('calls onSuccess after successful registration', async () => {
    render(<WorkerRegistration onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it('shows submitting state', async () => {
    mockRegisterWorker.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<WorkerRegistration />);

    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    fireEvent.click(screen.getByTestId('submit-button'));

    expect(screen.getByText('Registering...')).toBeInTheDocument();
    expect(screen.getByTestId('submit-button')).toBeDisabled();
  });

  it('shows error on registration failure', async () => {
    mockRegisterWorker.mockRejectedValue(new Error('Registration failed'));

    render(<WorkerRegistration />);

    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toBeInTheDocument();
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });

  it('shows cancel button when onCancel provided', () => {
    render(<WorkerRegistration onCancel={mockOnCancel} />);
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('calls onCancel when cancel clicked', () => {
    render(<WorkerRegistration onCancel={mockOnCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('toggles capabilities on click', () => {
    render(<WorkerRegistration />);

    const codeReview = screen.getByTestId('cap-code_review');

    // Initially unchecked
    expect(codeReview).not.toBeChecked();

    // Click to check
    fireEvent.click(codeReview);
    expect(codeReview).toBeChecked();

    // Click to uncheck
    fireEvent.click(codeReview);
    expect(codeReview).not.toBeChecked();
  });

  it('parses comma-separated labels', async () => {
    render(<WorkerRegistration />);

    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    fireEvent.change(screen.getByTestId('labels-input'), {
      target: { value: 'python, typescript, rust' }
    });

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockRegisterWorker).toHaveBeenCalledWith(
        expect.objectContaining({
          labels: ['python', 'typescript', 'rust']
        })
      );
    });
  });

  it('filters empty labels', async () => {
    render(<WorkerRegistration />);

    fireEvent.change(screen.getByTestId('name-input'), {
      target: { value: 'Test Worker' }
    });

    fireEvent.change(screen.getByTestId('labels-input'), {
      target: { value: 'python, , , rust' }
    });

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockRegisterWorker).toHaveBeenCalledWith(
        expect.objectContaining({
          labels: ['python', 'rust']
        })
      );
    });
  });
});
