/**
 * StoryCard component for mobile
 * Displays a story card with status indicators
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import type { Story } from '../../../shared/types';
import { colors, spacing, borderRadius, shadows } from '../theme';

interface StoryCardProps {
  story: Story;
  onPress: (story: Story) => void;
  compact?: boolean;
}

export function StoryCard({ story, onPress, compact = false }: StoryCardProps) {
  const priorityColor = getPriorityColor(story.priority);
  const hasFailedValidation = story.validation_result?.status === 'failed';
  const hasWarnings = story.skill_progress && hasIncompleteSkills(story.skill_progress);
  const isSuccess = story.column === 'done';

  // Determine border color based on semantic status
  const borderColor = hasFailedValidation
    ? colors.status.failure
    : hasWarnings
    ? colors.status.warning
    : isSuccess
    ? colors.status.success
    : colors.dashboard.border;

  return (
    <TouchableOpacity
      style={[
        styles.card,
        { borderLeftColor: borderColor, borderLeftWidth: 4 },
        compact && styles.cardCompact,
      ]}
      onPress={() => onPress(story)}
      activeOpacity={0.7}
    >
      {/* Priority indicator */}
      {story.priority && (
        <View style={[styles.priorityBadge, { backgroundColor: priorityColor }]}>
          <Text style={styles.priorityText}>{story.priority.charAt(0).toUpperCase()}</Text>
        </View>
      )}

      {/* Title */}
      <Text style={styles.title} numberOfLines={compact ? 1 : 2}>
        {story.title}
      </Text>

      {/* Labels */}
      {story.labels && story.labels.length > 0 && (
        <View style={styles.labels}>
          {story.labels.slice(0, 3).map((label) => (
            <View key={label} style={styles.label}>
              <Text style={styles.labelText}>{label}</Text>
            </View>
          ))}
          {story.labels.length > 3 && (
            <Text style={styles.moreLabels}>+{story.labels.length - 3}</Text>
          )}
        </View>
      )}

      {/* Footer: assignee, status indicators */}
      <View style={styles.footer}>
        {story.assignee && (
          <View style={styles.assignee}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {story.assignee.charAt(0).toUpperCase()}
              </Text>
            </View>
            {!compact && <Text style={styles.assigneeName}>{story.assignee}</Text>}
          </View>
        )}

        <View style={styles.statusIcons}>
          {/* Validation status */}
          {story.validation_result && (
            <View
              style={[
                styles.statusDot,
                {
                  backgroundColor:
                    story.validation_result.status === 'passed'
                      ? colors.status.success
                      : colors.status.failure,
                },
              ]}
            />
          )}

          {/* Agent assigned */}
          {story.assigned_worker && (
            <View style={[styles.statusDot, { backgroundColor: colors.agent.working }]} />
          )}

          {/* Comments count */}
          {story.comments && story.comments.length > 0 && (
            <Text style={styles.commentCount}>{story.comments.length}</Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

function getPriorityColor(priority?: string): string {
  switch (priority) {
    case 'critical':
      return colors.priority.critical;
    case 'high':
      return colors.priority.high;
    case 'medium':
      return colors.priority.medium;
    case 'low':
      return colors.priority.low;
    default:
      return colors.dashboard.textMuted;
  }
}

function hasIncompleteSkills(skillProgress: Story['skill_progress']): boolean {
  return Object.values(skillProgress).some(
    (skill) => skill.status === 'pending' || skill.status === 'in_progress'
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.dashboard.background,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.md,
  },
  cardCompact: {
    padding: spacing.sm,
  },
  priorityBadge: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    width: 20,
    height: 20,
    borderRadius: borderRadius.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  priorityText: {
    color: colors.dashboard.background,
    fontSize: 10,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.dashboard.text,
    marginBottom: spacing.sm,
    paddingRight: 24, // space for priority badge
  },
  labels: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: spacing.sm,
  },
  label: {
    backgroundColor: colors.dashboard.primaryLight,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    marginRight: spacing.xs,
    marginBottom: spacing.xs,
  },
  labelText: {
    fontSize: 10,
    color: colors.dashboard.primary,
  },
  moreLabels: {
    fontSize: 10,
    color: colors.dashboard.textMuted,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  assignee: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.dashboard.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.dashboard.text,
    fontSize: 12,
    fontWeight: 'bold',
  },
  assigneeName: {
    marginLeft: spacing.xs,
    fontSize: 12,
    color: colors.dashboard.textSecondary,
  },
  statusIcons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: spacing.xs,
  },
  commentCount: {
    fontSize: 10,
    color: colors.dashboard.textMuted,
    marginLeft: spacing.xs,
  },
});
