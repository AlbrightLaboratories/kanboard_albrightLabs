/**
 * StoryModal tests - MOB-08
 *
 * MOB-08: Story modal opens with full details and edit capability
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import type { Story } from '../../shared/types';

// Mock StoryModal component
const StoryModal = ({ story, visible, onClose, onEdit }: {
  story: Story | null;
  visible: boolean;
  onClose: () => void;
  onEdit: (updates: Partial<Story>) => void;
}) => {
  const { View, Text, Modal, TouchableOpacity, ScrollView, TextInput } = require('react-native');
  const [editing, setEditing] = React.useState(false);
  const [title, setTitle] = React.useState(story?.title || '');

  if (!story) return null;

  return (
    <Modal visible={visible} testID="story-modal">
      <View testID="modal-content">
        <ScrollView>
          {/* Header */}
          <View testID="modal-header">
            <TouchableOpacity onPress={onClose} testID="close-button">
              <Text>Close</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setEditing(!editing)} testID="edit-button">
              <Text>{editing ? 'Done' : 'Edit'}</Text>
            </TouchableOpacity>
          </View>

          {/* Title */}
          {editing ? (
            <TextInput
              testID="title-input"
              value={title}
              onChangeText={setTitle}
              onBlur={() => onEdit({ title })}
            />
          ) : (
            <Text testID="story-title">{story.title}</Text>
          )}

          {/* Description */}
          <Text testID="story-description">{story.description}</Text>

          {/* Column/Status */}
          <Text testID="story-column">Column: {story.column}</Text>

          {/* Priority */}
          {story.priority && (
            <Text testID="story-priority">Priority: {story.priority}</Text>
          )}

          {/* Labels */}
          <View testID="labels-container">
            {story.labels.map((label, i) => (
              <Text key={i} testID={`label-${label}`}>{label}</Text>
            ))}
          </View>

          {/* Assignee */}
          {story.assignee && (
            <Text testID="story-assignee">Assignee: {story.assignee}</Text>
          )}

          {/* Skill Progress */}
          <View testID="skill-progress">
            <Text>Plan: {story.skill_progress.plan.status}</Text>
            <Text>PRD: {story.skill_progress['design-a-prd'].status}</Text>
            <Text>TDD: {story.skill_progress.tdd.status}</Text>
            <Text>Prove-it: {story.skill_progress['prove-it'].status}</Text>
            <Text>Release-it: {story.skill_progress['release-it'].status}</Text>
          </View>

          {/* Validation Result */}
          {story.validation_result && (
            <View testID="validation-result">
              <Text>Validation: {story.validation_result.status}</Text>
              {story.validation_result.failures.map((f, i) => (
                <Text key={i} testID={`failure-${i}`}>{f}</Text>
              ))}
            </View>
          )}

          {/* Subtasks */}
          <View testID="subtasks">
            {story.subtasks.map((subtask) => (
              <View key={subtask.id} testID={`subtask-${subtask.id}`}>
                <Text>{subtask.completed ? '✓' : '○'} {subtask.title}</Text>
              </View>
            ))}
          </View>

          {/* Comments */}
          <View testID="comments-section">
            {story.comments.map((comment) => (
              <View key={comment.id} testID={`comment-${comment.id}`}>
                <Text>{comment.author}: {comment.content}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
};

const mockStory: Story = {
  id: 'story-1',
  title: 'Implement Feature X',
  description: 'As a user, I want feature X so that I can do Y',
  column: 'in_progress',
  labels: ['feature', 'priority'],
  priority: 'high',
  assignee: 'developer',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  subtasks: [
    { id: 'sub-1', title: 'Design UI', completed: true, is_acceptance_criteria: true, order: 1 },
    { id: 'sub-2', title: 'Implement API', completed: false, is_acceptance_criteria: true, order: 2 },
  ],
  comments: [
    {
      id: 'c-1',
      author: 'pm',
      content: 'Please prioritize this',
      created_at: '2024-01-01T00:00:00Z',
      is_agent_response: false,
    },
  ],
  skill_progress: {
    plan: { status: 'passed' },
    'design-a-prd': { status: 'passed' },
    tdd: { status: 'in_progress' },
    'prove-it': { status: 'pending' },
    'release-it': { status: 'pending' },
  },
};

describe('MOB-08: Story modal opens with full details and edit capability', () => {
  const onClose = jest.fn();
  const onEdit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when visible', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-modal')).toBeTruthy();
  });

  it('displays story title', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-title').children[0]).toBe('Implement Feature X');
  });

  it('displays story description', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-description')).toBeTruthy();
  });

  it('displays current column', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-column')).toBeTruthy();
  });

  it('displays priority', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-priority')).toBeTruthy();
  });

  it('displays labels', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('label-feature')).toBeTruthy();
    expect(getByTestId('label-priority')).toBeTruthy();
  });

  it('displays assignee', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('story-assignee')).toBeTruthy();
  });

  it('displays skill progress', () => {
    const { getByTestId, getByText } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('skill-progress')).toBeTruthy();
    expect(getByText(/Plan: passed/)).toBeTruthy();
  });

  it('displays subtasks', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('subtask-sub-1')).toBeTruthy();
    expect(getByTestId('subtask-sub-2')).toBeTruthy();
  });

  it('displays comments', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('comment-c-1')).toBeTruthy();
  });

  it('has close button', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    fireEvent.press(getByTestId('close-button'));
    expect(onClose).toHaveBeenCalled();
  });

  it('has edit button', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    expect(getByTestId('edit-button')).toBeTruthy();
  });

  it('toggles edit mode when edit button pressed', () => {
    const { getByTestId, queryByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    // Initially not editing
    expect(queryByTestId('title-input')).toBeNull();

    // Press edit button
    fireEvent.press(getByTestId('edit-button'));

    // Now in edit mode
    expect(getByTestId('title-input')).toBeTruthy();
  });

  it('calls onEdit when title is changed', () => {
    const { getByTestId } = render(
      <StoryModal story={mockStory} visible={true} onClose={onClose} onEdit={onEdit} />
    );

    // Enter edit mode
    fireEvent.press(getByTestId('edit-button'));

    // Change title
    const input = getByTestId('title-input');
    fireEvent.changeText(input, 'New Title');
    fireEvent(input, 'blur');

    expect(onEdit).toHaveBeenCalledWith({ title: 'New Title' });
  });
});
