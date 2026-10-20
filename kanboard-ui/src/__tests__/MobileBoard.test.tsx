/**
 * Tests for UI-10: Mobile responsive swipe between columns on <768px
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MobileBoard } from '../components/board/MobileBoard';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useStories: vi.fn(),
  useColumns: vi.fn()
}));

// Mock window.innerWidth
const setWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width
  });
  window.dispatchEvent(new Event('resize'));
};

describe('MobileBoard - UI-10', () => {
  const mockOnStoryClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Set mobile width
    setWindowWidth(375);

    vi.mocked(hooks.useColumns).mockReturnValue({
      columns: [
        { id: 1, title: 'Backlog', position: 1, project_id: 1 },
        { id: 2, title: 'In Progress', position: 2, project_id: 1 },
        { id: 3, title: 'Done', position: 3, project_id: 1 }
      ],
      loading: false
    });

    vi.mocked(hooks.useStories).mockReturnValue({
      stories: [
        { id: 101, title: 'Story 1', description: 'Test', column_id: 1, project_id: 1, owner_id: 0, priority: 2, position: 1 },
        { id: 102, title: 'Story 2', description: 'Test', column_id: 1, project_id: 1, owner_id: 0, priority: 2, position: 2 },
        { id: 103, title: 'Story 3', description: 'Test', column_id: 2, project_id: 1, owner_id: 0, priority: 3, position: 1 }
      ],
      loading: false,
      error: null,
      refresh: vi.fn(),
      moveStory: vi.fn()
    });
  });

  it('renders mobile board on small screen', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByTestId('mobile-board')).toBeInTheDocument();
  });

  it('does not render on large screen', () => {
    setWindowWidth(1024);
    const { container } = render(<MobileBoard projectId={1} />);
    expect(container.firstChild).toBeNull();
  });

  it('shows column tabs', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByTestId('column-tabs')).toBeInTheDocument();
    expect(screen.getByTestId('tab-1')).toBeInTheDocument();
    expect(screen.getByTestId('tab-2')).toBeInTheDocument();
    expect(screen.getByTestId('tab-3')).toBeInTheDocument();
  });

  it('shows column names in tabs', () => {
    render(<MobileBoard projectId={1} />);
    // Column names appear in tabs and may appear in active column header too
    expect(screen.getAllByText('Backlog').length).toBeGreaterThan(0);
    expect(screen.getAllByText('In Progress').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Done').length).toBeGreaterThan(0);
  });

  it('shows story count in tabs', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByText('(2)')).toBeInTheDocument(); // Backlog has 2 stories
    expect(screen.getByText('(1)')).toBeInTheDocument(); // In Progress has 1 story
    expect(screen.getByText('(0)')).toBeInTheDocument(); // Done has 0 stories
  });

  it('shows swipe indicator dots', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByTestId('swipe-indicator')).toBeInTheDocument();
  });

  it('shows active column content', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByTestId('mobile-column-1')).toBeInTheDocument();
  });

  it('shows stories in active column', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByText('Story 1')).toBeInTheDocument();
    expect(screen.getByText('Story 2')).toBeInTheDocument();
  });

  it('changes column on tab click', () => {
    render(<MobileBoard projectId={1} />);
    fireEvent.click(screen.getByTestId('tab-2'));
    expect(screen.getByTestId('mobile-column-2')).toBeInTheDocument();
    expect(screen.getByText('Story 3')).toBeInTheDocument();
  });

  it('shows swipe hint for next column', () => {
    render(<MobileBoard projectId={1} />);
    expect(screen.getByTestId('swipe-hint-right')).toBeInTheDocument();
    expect(screen.getByText(/In Progress →/)).toBeInTheDocument();
  });

  it('shows swipe hint for previous column', () => {
    render(<MobileBoard projectId={1} />);
    fireEvent.click(screen.getByTestId('tab-2'));
    expect(screen.getByTestId('swipe-hint-left')).toBeInTheDocument();
    expect(screen.getByText(/← Backlog/)).toBeInTheDocument();
  });

  it('handles swipe left to next column', () => {
    render(<MobileBoard projectId={1} />);
    const board = screen.getByTestId('mobile-board');

    // Simulate swipe left (start at 200, end at 100)
    fireEvent.touchStart(board, { touches: [{ clientX: 200 }] });
    fireEvent.touchMove(board, { touches: [{ clientX: 100 }] });
    fireEvent.touchEnd(board);

    // Should now be on second column
    expect(screen.getByTestId('mobile-column-2')).toBeInTheDocument();
  });

  it('handles swipe right to previous column', () => {
    render(<MobileBoard projectId={1} />);

    // First go to second column
    fireEvent.click(screen.getByTestId('tab-2'));
    expect(screen.getByTestId('mobile-column-2')).toBeInTheDocument();

    const board = screen.getByTestId('mobile-board');

    // Simulate swipe right (start at 100, end at 200)
    fireEvent.touchStart(board, { touches: [{ clientX: 100 }] });
    fireEvent.touchMove(board, { touches: [{ clientX: 200 }] });
    fireEvent.touchEnd(board);

    // Should now be back on first column
    expect(screen.getByTestId('mobile-column-1')).toBeInTheDocument();
  });

  it('ignores small swipes', () => {
    render(<MobileBoard projectId={1} />);
    const board = screen.getByTestId('mobile-board');

    // Simulate tiny swipe (less than 50px threshold)
    fireEvent.touchStart(board, { touches: [{ clientX: 200 }] });
    fireEvent.touchMove(board, { touches: [{ clientX: 180 }] });
    fireEvent.touchEnd(board);

    // Should still be on first column
    expect(screen.getByTestId('mobile-column-1')).toBeInTheDocument();
  });

  it('does not swipe past first column', () => {
    render(<MobileBoard projectId={1} />);
    const board = screen.getByTestId('mobile-board');

    // Simulate swipe right when already on first column
    fireEvent.touchStart(board, { touches: [{ clientX: 100 }] });
    fireEvent.touchMove(board, { touches: [{ clientX: 200 }] });
    fireEvent.touchEnd(board);

    // Should still be on first column
    expect(screen.getByTestId('mobile-column-1')).toBeInTheDocument();
  });

  it('does not swipe past last column', () => {
    render(<MobileBoard projectId={1} />);

    // Go to last column
    fireEvent.click(screen.getByTestId('tab-3'));

    const board = screen.getByTestId('mobile-board');

    // Simulate swipe left when already on last column
    fireEvent.touchStart(board, { touches: [{ clientX: 200 }] });
    fireEvent.touchMove(board, { touches: [{ clientX: 100 }] });
    fireEvent.touchEnd(board);

    // Should still be on last column
    expect(screen.getByTestId('mobile-column-3')).toBeInTheDocument();
  });

  it('calls onStoryClick when story clicked', () => {
    render(<MobileBoard projectId={1} onStoryClick={mockOnStoryClick} />);
    fireEvent.click(screen.getByTestId('card-101'));
    expect(mockOnStoryClick).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useStories).mockReturnValue({
      stories: [],
      loading: true,
      error: null,
      refresh: vi.fn(),
      moveStory: vi.fn()
    });

    render(<MobileBoard projectId={1} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows empty column message', () => {
    render(<MobileBoard projectId={1} />);
    fireEvent.click(screen.getByTestId('tab-3')); // Done column has no stories
    expect(screen.getByText('No stories')).toBeInTheDocument();
  });
});
