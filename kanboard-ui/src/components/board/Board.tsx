/**
 * Board Component
 *
 * Main board with columns and draggable cards.
 * Implements UI-01 and UI-02.
 */

import React, { useState } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter
} from '@dnd-kit/core';
import { Column } from './Column';
import { Card } from './Card';
import { useStories, useColumns } from '../../hooks/useKanboard';
import { Story } from '../../api/kanboard';

export interface BoardProps {
  projectId: number;
  onStoryClick?: (story: Story) => void;
}

export function Board({ projectId, onStoryClick }: BoardProps) {
  const { stories, moveStory, loading: storiesLoading } = useStories(projectId);
  const { columns, loading: columnsLoading } = useColumns(projectId);
  const [activeStory, setActiveStory] = useState<Story | null>(null);

  const handleDragStart = (event: DragStartEvent) => {
    const story = stories.find(s => s.id === event.active.id);
    setActiveStory(story || null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveStory(null);

    const { active, over } = event;
    if (!over) return;

    const storyId = active.id as number;
    const columnId = over.id as number;

    const story = stories.find(s => s.id === storyId);
    if (story && story.column_id !== columnId) {
      await moveStory(storyId, columnId);
    }
  };

  const getStoriesForColumn = (columnId: number) => {
    return stories
      .filter(s => s.column_id === columnId)
      .sort((a, b) => a.position - b.position);
  };

  if (storiesLoading || columnsLoading) {
    return <div className="board-loading">Loading...</div>;
  }

  return (
    <DndContext
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="board" data-testid="board">
        {columns
          .sort((a, b) => a.position - b.position)
          .map(column => (
            <Column
              key={column.id}
              column={column}
              stories={getStoriesForColumn(column.id)}
              onStoryClick={onStoryClick}
            />
          ))}
      </div>
      <DragOverlay>
        {activeStory && <Card story={activeStory} isDragging />}
      </DragOverlay>
    </DndContext>
  );
}

export default Board;
