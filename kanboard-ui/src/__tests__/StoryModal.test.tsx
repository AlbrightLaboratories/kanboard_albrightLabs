/**
 * Tests for UI-03: Story modal shows all JIRA-like fields
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StoryModal } from '../components/story/StoryModal';
import { Story } from '../api/kanboard';

// Mock API
vi.mock('../api/kanboard', () => ({
  kanboardAPI: {
    updateStory: vi.fn().mockResolvedValue(undefined)
  }
}));

describe('StoryModal - UI-03', () => {
  const mockStory: Story = {
    id: 123,
    title: 'Test Story Title',
    description: 'Detailed description with acceptance criteria',
    column_id: 1,
    project_id: 1,
    owner_id: 42,
    priority: 3,
    position: 1,
    worker_labels: ['python', 'backend'],
    assigned_worker: 'claude-001'
  };

  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal overlay', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-modal')).toBeInTheDocument();
  });

  it('shows story ID', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByText('#123')).toBeInTheDocument();
  });

  it('shows story title', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-title')).toHaveTextContent('Test Story Title');
  });

  it('shows description', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-description')).toHaveTextContent(
      'Detailed description with acceptance criteria'
    );
  });

  it('shows priority', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-priority')).toHaveTextContent('High');
  });

  it('shows assignee', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-assignee')).toHaveTextContent('User #42');
  });

  it('shows worker labels', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('worker-labels')).toBeInTheDocument();
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('backend')).toBeInTheDocument();
  });

  it('shows assigned worker', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('assigned-worker')).toHaveTextContent('claude-001');
  });

  it('has edit button', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('edit-button')).toBeInTheDocument();
  });

  it('shows edit form when edit clicked', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    fireEvent.click(screen.getByTestId('edit-button'));

    expect(screen.getByTestId('title-input')).toBeInTheDocument();
    expect(screen.getByTestId('description-input')).toBeInTheDocument();
    expect(screen.getByTestId('priority-select')).toBeInTheDocument();
  });

  it('close button calls onClose', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    fireEvent.click(screen.getByText('×'));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('clicking overlay calls onClose', () => {
    render(<StoryModal story={mockStory} onClose={mockOnClose} />);
    fireEvent.click(screen.getByTestId('story-modal'));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows Unassigned when no owner', () => {
    const unassignedStory = { ...mockStory, owner_id: 0 };
    render(<StoryModal story={unassignedStory} onClose={mockOnClose} />);
    expect(screen.getByTestId('story-assignee')).toHaveTextContent('Unassigned');
  });
});
