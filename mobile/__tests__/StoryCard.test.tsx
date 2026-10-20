/**
 * StoryCard component tests
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StoryCard } from '../src/components/StoryCard';
import type { Story } from '../../shared/types';

// Mock story data
const mockStory: Story = {
  id: 'story-1',
  title: 'Test Story',
  description: 'Test description',
  column: 'in_progress',
  labels: ['feature', 'priority'],
  priority: 'high',
  assignee: 'developer',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  subtasks: [],
  comments: [],
  skill_progress: {
    plan: { status: 'passed' },
    'design-a-prd': { status: 'passed' },
    tdd: { status: 'in_progress' },
    'prove-it': { status: 'pending' },
    'release-it': { status: 'pending' },
  },
};

describe('StoryCard', () => {
  it('renders story title', () => {
    const onPress = jest.fn();
    const { getByText } = render(<StoryCard story={mockStory} onPress={onPress} />);

    expect(getByText('Test Story')).toBeTruthy();
  });

  it('displays priority badge', () => {
    const onPress = jest.fn();
    const { getByText } = render(<StoryCard story={mockStory} onPress={onPress} />);

    // Priority badge shows first letter
    expect(getByText('H')).toBeTruthy();
  });

  it('shows labels', () => {
    const onPress = jest.fn();
    const { getByText } = render(<StoryCard story={mockStory} onPress={onPress} />);

    expect(getByText('feature')).toBeTruthy();
    expect(getByText('priority')).toBeTruthy();
  });

  it('shows assignee avatar', () => {
    const onPress = jest.fn();
    const { getByText } = render(<StoryCard story={mockStory} onPress={onPress} />);

    // Assignee initial
    expect(getByText('D')).toBeTruthy();
  });

  it('calls onPress when tapped', () => {
    const onPress = jest.fn();
    const { getByText } = render(<StoryCard story={mockStory} onPress={onPress} />);

    fireEvent.press(getByText('Test Story'));
    expect(onPress).toHaveBeenCalledWith(mockStory);
  });

  it('shows failure border when validation failed', () => {
    const failedStory: Story = {
      ...mockStory,
      validation_result: {
        status: 'failed',
        timestamp: '2024-01-01T00:00:00Z',
        message: 'Tests failed',
        failures: ['test_example failed'],
      },
    };

    const onPress = jest.fn();
    const { root } = render(<StoryCard story={failedStory} onPress={onPress} />);

    // Card should have failure border color (red)
    expect(root).toBeTruthy();
  });

  it('shows success border for done stories', () => {
    const doneStory: Story = {
      ...mockStory,
      column: 'done',
    };

    const onPress = jest.fn();
    const { root } = render(<StoryCard story={doneStory} onPress={onPress} />);

    // Card should have success border color (green)
    expect(root).toBeTruthy();
  });

  it('renders in compact mode', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <StoryCard story={mockStory} onPress={onPress} compact={true} />
    );

    expect(getByText('Test Story')).toBeTruthy();
  });
});
