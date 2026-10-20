/**
 * Tests for UI-09: Dependency graph mini-map renders story relationships
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DependencyGraph } from '../components/board/DependencyGraph';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useDependencyGraph: vi.fn()
}));

describe('DependencyGraph - UI-09', () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dependency graph', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker Story' },
          { id: 200, title: 'Blocked Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' },
          { from: 123, to: 200, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('dependency-graph')).toBeInTheDocument();
  });

  it('shows story nodes', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('node-123')).toBeInTheDocument();
    expect(screen.getByTestId('node-100')).toBeInTheDocument();
  });

  it('shows story ID in nodes', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByText('#123')).toBeInTheDocument();
    expect(screen.getByText('#100')).toBeInTheDocument();
  });

  it('shows edges between nodes', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('edge-100-123')).toBeInTheDocument();
  });

  it('shows multiple edges', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker 1' },
          { id: 101, title: 'Blocker 2' },
          { id: 200, title: 'Blocked Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' },
          { from: 101, to: 123, type: 'blocks' },
          { from: 123, to: 200, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('edge-100-123')).toBeInTheDocument();
    expect(screen.getByTestId('edge-101-123')).toBeInTheDocument();
    expect(screen.getByTestId('edge-123-200')).toBeInTheDocument();
  });

  it('highlights main story node', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Other Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    // Main node should have larger radius (25 vs 20)
    const mainNode = screen.getByTestId('node-123');
    const circle = mainNode.querySelector('circle');
    expect(circle).toHaveAttribute('r', '25');
  });

  it('calls onClick when node clicked', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [
          { id: 123, title: 'Main Story' },
          { id: 100, title: 'Blocker Story' }
        ],
        edges: [
          { from: 100, to: 123, type: 'blocks' }
        ]
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} onClick={mockOnClick} />);
    fireEvent.click(screen.getByTestId('node-100'));
    expect(mockOnClick).toHaveBeenCalledWith(100);
  });

  it('shows legend', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: {
        nodes: [{ id: 123, title: 'Story' }],
        edges: []
      },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByText('Blockers')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: null,
      loading: true
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows no dependencies message when empty', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: { nodes: [], edges: [] },
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('no-dependencies')).toBeInTheDocument();
    expect(screen.getByText('No dependencies')).toBeInTheDocument();
  });

  it('shows no dependencies when graph is null', () => {
    vi.mocked(hooks.useDependencyGraph).mockReturnValue({
      graph: null,
      loading: false
    });

    render(<DependencyGraph storyId={123} />);
    expect(screen.getByTestId('no-dependencies')).toBeInTheDocument();
  });
});
