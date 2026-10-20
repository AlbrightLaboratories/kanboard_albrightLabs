/**
 * BoardScreen - Mobile board with swipe navigation
 *
 * On mobile (<768px):
 * - Single column view
 * - Swipe left/right to navigate between columns
 * - Tab bar at bottom for quick column access
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Dimensions,
  TouchableOpacity,
  RefreshControl,
  Animated,
} from 'react-native';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import type { Story, StoryColumn } from '../../../shared/types';
import { colors, spacing, borderRadius } from '../theme';
import { StoryCard } from '../components/StoryCard';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Column definitions
const COLUMNS: { id: StoryColumn; name: string; color: string }[] = [
  { id: 'backlog', name: 'Backlog', color: colors.columns.backlog },
  { id: 'groomed', name: 'Groomed', color: colors.columns.groomed },
  { id: 'in_progress', name: 'In Progress', color: colors.columns.in_progress },
  { id: 'validation', name: 'Validation', color: colors.columns.validation },
  { id: 'done', name: 'Done', color: colors.columns.done },
];

interface BoardScreenProps {
  stories: Story[];
  onStoryPress: (story: Story) => void;
  onRefresh: () => Promise<void>;
  loading: boolean;
}

export function BoardScreen({
  stories,
  onStoryPress,
  onRefresh,
  loading,
}: BoardScreenProps) {
  const [currentColumnIndex, setCurrentColumnIndex] = useState(0);
  const translateX = useRef(new Animated.Value(0)).current;

  // Get stories for current column
  const currentColumn = COLUMNS[currentColumnIndex];
  const columnStories = stories.filter((s) => s.column === currentColumn.id);

  // Swipe gesture handler
  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: translateX } }],
    { useNativeDriver: true }
  );

  const onHandlerStateChange = useCallback(
    ({ nativeEvent }: { nativeEvent: { state: number; translationX: number } }) => {
      if (nativeEvent.state === State.END) {
        const { translationX: tx } = nativeEvent;

        // Swipe threshold
        if (Math.abs(tx) > SCREEN_WIDTH * 0.25) {
          if (tx > 0 && currentColumnIndex > 0) {
            // Swipe right - go to previous column
            setCurrentColumnIndex((prev) => prev - 1);
          } else if (tx < 0 && currentColumnIndex < COLUMNS.length - 1) {
            // Swipe left - go to next column
            setCurrentColumnIndex((prev) => prev + 1);
          }
        }

        // Reset animation
        Animated.spring(translateX, {
          toValue: 0,
          useNativeDriver: true,
        }).start();
      }
    },
    [currentColumnIndex, translateX]
  );

  // Navigate to specific column
  const navigateToColumn = useCallback((index: number) => {
    setCurrentColumnIndex(index);
  }, []);

  // Count stories per column
  const getColumnCount = useCallback(
    (columnId: StoryColumn): number => {
      return stories.filter((s) => s.column === columnId).length;
    },
    [stories]
  );

  // Render story item
  const renderStory = useCallback(
    ({ item }: { item: Story }) => (
      <StoryCard story={item} onPress={onStoryPress} compact={false} />
    ),
    [onStoryPress]
  );

  return (
    <View style={styles.container}>
      {/* Column header */}
      <View style={[styles.header, { backgroundColor: currentColumn.color }]}>
        <View style={styles.headerContent}>
          <Text style={styles.columnName}>{currentColumn.name}</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{columnStories.length}</Text>
          </View>
        </View>

        {/* Column navigation arrows */}
        <View style={styles.navArrows}>
          {currentColumnIndex > 0 && (
            <TouchableOpacity
              style={styles.navArrow}
              onPress={() => navigateToColumn(currentColumnIndex - 1)}
            >
              <Text style={styles.navArrowText}>{'<'}</Text>
            </TouchableOpacity>
          )}
          {currentColumnIndex < COLUMNS.length - 1 && (
            <TouchableOpacity
              style={styles.navArrow}
              onPress={() => navigateToColumn(currentColumnIndex + 1)}
            >
              <Text style={styles.navArrowText}>{'>'}</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Swipeable story list */}
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
      >
        <Animated.View
          style={[
            styles.cardContainer,
            {
              transform: [
                {
                  translateX: translateX.interpolate({
                    inputRange: [-SCREEN_WIDTH, 0, SCREEN_WIDTH],
                    outputRange: [-50, 0, 50],
                    extrapolate: 'clamp',
                  }),
                },
              ],
            },
          ]}
        >
          <FlatList
            data={columnStories}
            renderItem={renderStory}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={loading}
                onRefresh={onRefresh}
                colors={[colors.dashboard.primary]}
                tintColor={colors.dashboard.primary}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>No stories in {currentColumn.name}</Text>
              </View>
            }
          />
        </Animated.View>
      </PanGestureHandler>

      {/* Bottom tab bar for quick column access */}
      <View style={styles.tabBar}>
        {COLUMNS.map((column, index) => (
          <TouchableOpacity
            key={column.id}
            style={[
              styles.tab,
              index === currentColumnIndex && styles.tabActive,
            ]}
            onPress={() => navigateToColumn(index)}
          >
            <View
              style={[
                styles.tabIndicator,
                { backgroundColor: column.color },
                index === currentColumnIndex && styles.tabIndicatorActive,
              ]}
            />
            <Text
              style={[
                styles.tabText,
                index === currentColumnIndex && styles.tabTextActive,
              ]}
              numberOfLines={1}
            >
              {column.name}
            </Text>
            <View style={styles.tabCount}>
              <Text style={styles.tabCountText}>{getColumnCount(column.id)}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Swipe hint */}
      <Text style={styles.swipeHint}>
        Swipe left or right to change columns
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.dashboard.surface,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    paddingTop: spacing.xl, // Safe area
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  columnName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.dashboard.background,
  },
  countBadge: {
    marginLeft: spacing.sm,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: borderRadius.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  countText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.dashboard.background,
  },
  navArrows: {
    flexDirection: 'row',
  },
  navArrow: {
    padding: spacing.sm,
    marginLeft: spacing.xs,
  },
  navArrowText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.dashboard.background,
  },
  cardContainer: {
    flex: 1,
  },
  listContent: {
    padding: spacing.md,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xxl,
  },
  emptyText: {
    fontSize: 16,
    color: colors.dashboard.textMuted,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.dashboard.background,
    borderTopWidth: 1,
    borderTopColor: colors.dashboard.border,
    paddingBottom: spacing.md, // Safe area
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  tabActive: {
    backgroundColor: colors.dashboard.surfaceAlt,
  },
  tabIndicator: {
    width: 20,
    height: 4,
    borderRadius: 2,
    marginBottom: 4,
    opacity: 0.5,
  },
  tabIndicatorActive: {
    opacity: 1,
    width: 30,
  },
  tabText: {
    fontSize: 10,
    color: colors.dashboard.textMuted,
  },
  tabTextActive: {
    color: colors.dashboard.text,
    fontWeight: '600',
  },
  tabCount: {
    marginTop: 2,
    backgroundColor: colors.dashboard.surfaceAlt,
    borderRadius: borderRadius.full,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  tabCountText: {
    fontSize: 10,
    color: colors.dashboard.textSecondary,
  },
  swipeHint: {
    textAlign: 'center',
    fontSize: 11,
    color: colors.dashboard.textMuted,
    paddingVertical: spacing.xs,
    backgroundColor: colors.dashboard.background,
  },
});
