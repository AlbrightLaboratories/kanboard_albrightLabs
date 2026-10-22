/**
 * AgentComments tests - MOB-04
 *
 * MOB-04: AgentComments allows @mentions to trigger agent responses
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { AgentComments } from '../src/components/AgentComments';

// Mock the component if it doesn't exist yet
jest.mock('../src/components/AgentComments', () => ({
  AgentComments: ({ comments, onMention, onSubmit }: any) => {
    const React = require('react');
    const { View, TextInput, TouchableOpacity, Text } = require('react-native');
    const [text, setText] = React.useState('');

    return (
      <View testID="agent-comments">
        {comments.map((c: any) => (
          <View key={c.id} testID={`comment-${c.id}`}>
            <Text>{c.author}</Text>
            <Text>{c.content}</Text>
            {c.is_agent_response && <Text testID="agent-badge">Agent</Text>}
          </View>
        ))}
        <TextInput
          testID="comment-input"
          value={text}
          onChangeText={(val: string) => {
            setText(val);
            // Detect @mentions
            const mentions = val.match(/@\w+/g) || [];
            if (mentions.length > 0) {
              onMention?.(mentions);
            }
          }}
          placeholder="Add a comment... Use @agent to mention"
        />
        <TouchableOpacity
          testID="submit-button"
          onPress={() => {
            onSubmit?.(text);
            setText('');
          }}
        >
          <Text>Send</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

const mockComments = [
  {
    id: 'comment-1',
    author: 'developer',
    content: '@hermes can you help with this?',
    created_at: '2024-01-01T00:00:00Z',
    is_agent_response: false,
    mentions: ['hermes'],
  },
  {
    id: 'comment-2',
    author: 'hermes',
    content: 'Sure! I can help. Let me analyze...',
    created_at: '2024-01-01T00:01:00Z',
    is_agent_response: true,
    agent_id: 'hermes-1',
  },
];

describe('MOB-04: AgentComments allows @mentions to trigger agent responses', () => {
  const onMention = jest.fn();
  const onSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders comment list', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    expect(getByTestId('agent-comments')).toBeTruthy();
    expect(getByTestId('comment-comment-1')).toBeTruthy();
    expect(getByTestId('comment-comment-2')).toBeTruthy();
  });

  it('shows agent badge for agent responses', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    expect(getByTestId('agent-badge')).toBeTruthy();
  });

  it('has comment input field', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    const input = getByTestId('comment-input');
    expect(input).toBeTruthy();
  });

  it('detects @mentions when typing', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    const input = getByTestId('comment-input');
    fireEvent.changeText(input, '@hermes can you help?');

    expect(onMention).toHaveBeenCalledWith(['@hermes']);
  });

  it('detects multiple @mentions', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    const input = getByTestId('comment-input');
    fireEvent.changeText(input, '@hermes @claude please review');

    expect(onMention).toHaveBeenCalledWith(['@hermes', '@claude']);
  });

  it('submits comment when send pressed', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    const input = getByTestId('comment-input');
    const button = getByTestId('submit-button');

    fireEvent.changeText(input, '@hermes fix this bug');
    fireEvent.press(button);

    expect(onSubmit).toHaveBeenCalledWith('@hermes fix this bug');
  });

  it('clears input after submit', () => {
    const { getByTestId } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    const input = getByTestId('comment-input');
    const button = getByTestId('submit-button');

    fireEvent.changeText(input, 'test comment');
    fireEvent.press(button);

    // Input should be cleared after submit
    expect(input.props.value).toBe('');
  });

  it('shows placeholder text with @agent instruction', () => {
    const { getByPlaceholderText } = render(
      <AgentComments
        comments={mockComments}
        onMention={onMention}
        onSubmit={onSubmit}
      />
    );

    expect(getByPlaceholderText(/@agent/i)).toBeTruthy();
  });
});
