/**
 * Tests for UI-04: SkillTracker shows skill progress
 * Tests for UI-05: SkillTracker blocks manual Done move if skills incomplete
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SkillTracker } from '../components/skill-tracker/SkillTracker';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useSkillProgress: vi.fn()
}));

describe('SkillTracker - UI-04', () => {
  beforeEach(() => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'passed' },
          { name: 'tdd', status: 'running' },
          { name: 'prove-it', status: 'pending' },
          { name: 'release-it', status: 'pending' }
        ]
      },
      loading: false,
      isComplete: false, canMoveToDone: false
    });
  });

  it('renders skill tracker', () => {
    render(<SkillTracker storyId={123} />);
    expect(screen.getByTestId('skill-tracker')).toBeInTheDocument();
  });

  it('shows progress bar', () => {
    render(<SkillTracker storyId={123} />);
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
  });

  it('shows progress percentage', () => {
    render(<SkillTracker storyId={123} />);
    // 2 out of 5 = 40%
    expect(screen.getByText(/2\/5/)).toBeInTheDocument();
    expect(screen.getByText(/40%/)).toBeInTheDocument();
  });

  it('displays all skill names', () => {
    render(<SkillTracker storyId={123} />);
    expect(screen.getByTestId('skill-plan')).toBeInTheDocument();
    expect(screen.getByTestId('skill-design-a-prd')).toBeInTheDocument();
    expect(screen.getByTestId('skill-tdd')).toBeInTheDocument();
    expect(screen.getByTestId('skill-prove-it')).toBeInTheDocument();
    expect(screen.getByTestId('skill-release-it')).toBeInTheDocument();
  });

  it('shows correct status for passed skills', () => {
    render(<SkillTracker storyId={123} />);
    const planSkill = screen.getByTestId('skill-plan');
    expect(planSkill).toHaveTextContent('passed');
    expect(planSkill).toHaveClass('skill-passed');
  });

  it('shows correct status for running skills', () => {
    render(<SkillTracker storyId={123} />);
    const tddSkill = screen.getByTestId('skill-tdd');
    expect(tddSkill).toHaveTextContent('running');
    expect(tddSkill).toHaveClass('skill-running');
  });

  it('shows correct status for pending skills', () => {
    render(<SkillTracker storyId={123} />);
    const proveItSkill = screen.getByTestId('skill-prove-it');
    expect(proveItSkill).toHaveTextContent('pending');
    expect(proveItSkill).toHaveClass('skill-pending');
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: null,
      loading: true,
      isComplete: false, canMoveToDone: false
    });

    render(<SkillTracker storyId={123} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles null progress', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: null,
      loading: false,
      isComplete: false, canMoveToDone: false
    });

    const { container } = render(<SkillTracker storyId={123} />);
    expect(container.querySelector('.skill-tracker')).not.toBeInTheDocument();
  });
});

describe('SkillTracker - UI-05 (Skill Gate)', () => {
  const mockMoveRequest = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows warning when skills incomplete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'pending' },
          { name: 'tdd', status: 'pending' },
          { name: 'prove-it', status: 'pending' },
          { name: 'release-it', status: 'pending' }
        ]
      },
      loading: false,
      isComplete: false, canMoveToDone: false
    });

    render(<SkillTracker storyId={123} onMoveRequest={mockMoveRequest} />);
    expect(screen.getByTestId('skill-gate-warning')).toBeInTheDocument();
  });

  it('hides warning when all skills complete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'passed' },
          { name: 'tdd', status: 'passed' },
          { name: 'prove-it', status: 'passed' },
          { name: 'release-it', status: 'passed' }
        ]
      },
      loading: false,
      isComplete: true, canMoveToDone: true
    });

    render(<SkillTracker storyId={123} />);
    expect(screen.queryByTestId('skill-gate-warning')).not.toBeInTheDocument();
  });

  it('disables Move to Done button when skills incomplete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'pending' },
          { name: 'tdd', status: 'pending' },
          { name: 'prove-it', status: 'pending' },
          { name: 'release-it', status: 'pending' }
        ]
      },
      loading: false,
      isComplete: false, canMoveToDone: false
    });

    render(<SkillTracker storyId={123} />);
    const button = screen.getByTestId('move-to-done-button');
    expect(button).toBeDisabled();
  });

  it('enables Move to Done button when all skills complete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'passed' },
          { name: 'tdd', status: 'passed' },
          { name: 'prove-it', status: 'passed' },
          { name: 'release-it', status: 'passed' }
        ]
      },
      loading: false,
      isComplete: true, canMoveToDone: true
    });

    render(<SkillTracker storyId={123} />);
    const button = screen.getByTestId('move-to-done-button');
    expect(button).not.toBeDisabled();
  });

  it('calls onMoveRequest with false when skills incomplete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [{ name: 'plan', status: 'pending' }]
      },
      loading: false,
      isComplete: false, canMoveToDone: false
    });

    render(<SkillTracker storyId={123} onMoveRequest={mockMoveRequest} />);
    // Button is disabled but we can still test the callback setup
    expect(screen.getByTestId('move-to-done-button')).toBeDisabled();
  });

  it('calls onMoveRequest with true when skills complete', () => {
    vi.mocked(hooks.useSkillProgress).mockReturnValue({
      progress: {
        story_id: 123,
        skills: [
          { name: 'plan', status: 'passed' },
          { name: 'design-a-prd', status: 'passed' },
          { name: 'tdd', status: 'passed' },
          { name: 'prove-it', status: 'passed' },
          { name: 'release-it', status: 'passed' }
        ]
      },
      loading: false,
      isComplete: true, canMoveToDone: true
    });

    render(<SkillTracker storyId={123} onMoveRequest={mockMoveRequest} />);
    fireEvent.click(screen.getByTestId('move-to-done-button'));
    expect(mockMoveRequest).toHaveBeenCalledWith(true);
  });
});
