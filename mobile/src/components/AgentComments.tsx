/**
 * AgentComments component
 * Allows users to comment on stories and get AI agent responses
 *
 * Feature: Agent-in-comments
 * - User writes a comment mentioning @agent (e.g., @claude, @gemini)
 * - Agent receives the comment and responds in the thread
 * - When agent has enough context, it can continue work in sandbox pod
 * - Results from sandbox testing flow back as comments
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import type { Comment, Agent } from '../../../shared/types';
import { colors, spacing, borderRadius, shadows } from '../theme';
import { getKanboardApi } from '../../../shared/api/kanboard';

interface AgentCommentsProps {
  storyId: string;
  comments: Comment[];
  agents: Agent[];
  onCommentAdded: (comment: Comment) => void;
  onAgentResponse: (comment: Comment) => void;
}

export function AgentComments({
  storyId,
  comments,
  agents,
  onCommentAdded,
  onAgentResponse,
}: AgentCommentsProps) {
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingAgentResponses, setPendingAgentResponses] = useState<Set<string>>(new Set());

  const api = getKanboardApi();

  // Parse @mentions from comment text
  const parseMentions = useCallback((text: string): string[] => {
    const mentionRegex = /@(\w+)/g;
    const mentions: string[] = [];
    let match;
    while ((match = mentionRegex.exec(text)) !== null) {
      mentions.push(match[1].toLowerCase());
    }
    return mentions;
  }, []);

  // Check if any mentioned agent is available
  const findAvailableAgent = useCallback(
    (mentions: string[]): Agent | null => {
      for (const mention of mentions) {
        const agent = agents.find(
          (a) =>
            a.name.toLowerCase() === mention ||
            a.type.toLowerCase() === mention ||
            a.id.toLowerCase() === mention
        );
        if (agent && agent.status !== 'offline') {
          return agent;
        }
      }
      return null;
    },
    [agents]
  );

  // Submit comment
  const handleSubmit = useCallback(async () => {
    if (!newComment.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      const mentions = parseMentions(newComment);
      const response = await api.addComment(storyId, newComment, mentions);

      if (response.success && response.data) {
        onCommentAdded(response.data);
        setNewComment('');

        // Check if we need to trigger an agent response
        const agent = findAvailableAgent(mentions);
        if (agent) {
          setPendingAgentResponses((prev) => new Set(prev).add(response.data!.id));

          // Trigger agent response
          const agentResponse = await api.triggerAgentResponse(
            storyId,
            response.data.id,
            agent.id
          );

          if (agentResponse.success) {
            // Agent response will come via WebSocket, but we mark as pending
            console.log('Agent response triggered:', agentResponse.data?.execution_id);
          }
        }
      }
    } catch (error) {
      console.error('Failed to submit comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [newComment, storyId, isSubmitting, api, parseMentions, findAvailableAgent, onCommentAdded]);

  // Render a single comment
  const renderComment = ({ item }: { item: Comment }) => {
    const isAgentComment = item.is_agent_response;
    const isPending = pendingAgentResponses.has(item.id);

    return (
      <View
        style={[
          styles.comment,
          isAgentComment && styles.agentComment,
        ]}
      >
        {/* Author avatar and name */}
        <View style={styles.commentHeader}>
          <View
            style={[
              styles.avatar,
              isAgentComment && styles.agentAvatar,
            ]}
          >
            <Text style={styles.avatarText}>
              {isAgentComment ? 'AI' : item.author.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text style={styles.authorName}>
            {item.author}
            {isAgentComment && (
              <Text style={styles.agentBadge}> (Agent)</Text>
            )}
          </Text>
          <Text style={styles.timestamp}>
            {formatTimestamp(item.created_at)}
          </Text>
        </View>

        {/* Comment content */}
        <Text style={styles.commentContent}>
          {highlightMentions(item.content)}
        </Text>

        {/* Pending indicator for agent responses */}
        {isPending && (
          <View style={styles.pendingIndicator}>
            <ActivityIndicator size="small" color={colors.dashboard.primary} />
            <Text style={styles.pendingText}>Waiting for agent response...</Text>
          </View>
        )}

        {/* Agent action buttons */}
        {isAgentComment && item.content.includes('[READY_TO_EXECUTE]') && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.actionButton, styles.approveButton]}
              onPress={() => console.log('Approve sandbox execution')}
            >
              <Text style={styles.actionButtonText}>Approve & Execute</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.rejectButton]}
              onPress={() => console.log('Reject execution')}
            >
              <Text style={styles.actionButtonText}>Reject</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={100}
    >
      {/* Agent status bar */}
      <View style={styles.agentStatusBar}>
        <Text style={styles.agentStatusTitle}>Available Agents:</Text>
        {agents.filter((a) => a.status !== 'offline').map((agent) => (
          <View key={agent.id} style={styles.agentChip}>
            <View
              style={[
                styles.agentStatusDot,
                { backgroundColor: getAgentStatusColor(agent.status) },
              ]}
            />
            <Text style={styles.agentChipText}>@{agent.name}</Text>
          </View>
        ))}
      </View>

      {/* Comments list */}
      <FlatList
        data={comments}
        renderItem={renderComment}
        keyExtractor={(item) => item.id}
        style={styles.commentsList}
        inverted={false}
        contentContainerStyle={styles.commentsContent}
      />

      {/* New comment input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={newComment}
          onChangeText={setNewComment}
          placeholder="Add a comment... (use @claude or @gemini to mention an agent)"
          placeholderTextColor={colors.dashboard.textMuted}
          multiline
          maxLength={2000}
        />
        <TouchableOpacity
          style={[styles.sendButton, !newComment.trim() && styles.sendButtonDisabled]}
          onPress={handleSubmit}
          disabled={!newComment.trim() || isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color={colors.dashboard.background} />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Help text */}
      <Text style={styles.helpText}>
        Tip: Mention @agent to get AI assistance. The agent will respond in comments and can
        execute code in a sandbox when ready.
      </Text>
    </KeyboardAvoidingView>
  );
}

// Helper functions
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
}

function getAgentStatusColor(status: string): string {
  switch (status) {
    case 'idle':
      return colors.agent.idle;
    case 'working':
      return colors.agent.working;
    case 'validating':
      return colors.agent.validating;
    case 'blocked':
      return colors.agent.blocked;
    default:
      return colors.agent.offline;
  }
}

function highlightMentions(text: string): React.ReactNode {
  // This would return styled text with highlighted @mentions
  // Simplified for now
  return text;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.dashboard.surface,
  },
  agentStatusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.sm,
    backgroundColor: colors.dashboard.background,
    borderBottomWidth: 1,
    borderBottomColor: colors.dashboard.border,
  },
  agentStatusTitle: {
    fontSize: 12,
    color: colors.dashboard.textSecondary,
    marginRight: spacing.sm,
  },
  agentChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.dashboard.surfaceAlt,
    borderRadius: borderRadius.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    marginRight: spacing.xs,
  },
  agentStatusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  agentChipText: {
    fontSize: 12,
    color: colors.dashboard.text,
  },
  commentsList: {
    flex: 1,
  },
  commentsContent: {
    padding: spacing.md,
  },
  comment: {
    backgroundColor: colors.dashboard.background,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  agentComment: {
    backgroundColor: colors.dashboard.primaryLight,
    borderLeftWidth: 3,
    borderLeftColor: colors.dashboard.primary,
  },
  commentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.dashboard.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  agentAvatar: {
    backgroundColor: colors.dashboard.primary,
  },
  avatarText: {
    color: colors.dashboard.background,
    fontSize: 12,
    fontWeight: 'bold',
  },
  authorName: {
    marginLeft: spacing.sm,
    fontSize: 14,
    fontWeight: '600',
    color: colors.dashboard.text,
  },
  agentBadge: {
    fontWeight: 'normal',
    color: colors.dashboard.primary,
  },
  timestamp: {
    marginLeft: 'auto',
    fontSize: 11,
    color: colors.dashboard.textMuted,
  },
  commentContent: {
    fontSize: 14,
    color: colors.dashboard.text,
    lineHeight: 20,
  },
  pendingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: colors.dashboard.surfaceAlt,
    borderRadius: borderRadius.sm,
  },
  pendingText: {
    marginLeft: spacing.sm,
    fontSize: 12,
    color: colors.dashboard.textSecondary,
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: spacing.md,
  },
  actionButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    marginHorizontal: spacing.xs,
  },
  approveButton: {
    backgroundColor: colors.status.success,
  },
  rejectButton: {
    backgroundColor: colors.status.failure,
  },
  actionButtonText: {
    color: colors.dashboard.background,
    fontSize: 14,
    fontWeight: '600',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: spacing.md,
    backgroundColor: colors.dashboard.background,
    borderTopWidth: 1,
    borderTopColor: colors.dashboard.border,
  },
  input: {
    flex: 1,
    backgroundColor: colors.dashboard.surfaceAlt,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 14,
    color: colors.dashboard.text,
    maxHeight: 100,
  },
  sendButton: {
    marginLeft: spacing.sm,
    backgroundColor: colors.dashboard.primary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: colors.dashboard.textMuted,
  },
  sendButtonText: {
    color: colors.dashboard.background,
    fontWeight: '600',
  },
  helpText: {
    fontSize: 11,
    color: colors.dashboard.textMuted,
    textAlign: 'center',
    padding: spacing.sm,
    backgroundColor: colors.dashboard.background,
  },
});
