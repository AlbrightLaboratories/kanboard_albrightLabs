/**
 * Column Component
 *
 * Droppable column for stories.
 */

import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { Card } from './Card';
import { Story, Column as ColumnType } from '../../api/kanboard';

export interface ColumnProps {
  column: ColumnType;
  stories: Story[];
  onStoryClick?: (story: Story) => void;
}

export function Column({ column, stories, onStoryClick }: ColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id
  });

  return (
    <div
      ref={setNodeRef}
      className={`column ${isOver ? 'column-over' : ''}`}
      data-testid={`column-${column.id}`}
    >
      <div className="column-header">
        <h3>{column.title}</h3>
        <span className="story-count">{stories.length}</span>
      </div>
      <div className="column-content">
        {stories.map(story => (
          <Card
            key={story.id}
            story={story}
            onClick={() => onStoryClick?.(story)}
          />
        ))}
      </div>
    </div>
  );
}

export default Column;
