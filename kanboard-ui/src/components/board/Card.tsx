/**
 * Card Component
 *
 * Draggable story card.
 */

// import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { Story } from '../../api/kanboard';

export interface CardProps {
  story: Story;
  isDragging?: boolean;
  onClick?: () => void;
}

export function Card({ story, isDragging, onClick }: CardProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: story.id
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      }
    : undefined;

  const getPriorityClass = (priority: number) => {
    if (priority >= 3) return 'priority-high';
    if (priority >= 2) return 'priority-medium';
    return 'priority-low';
  };

  return (
    <div
      ref={setNodeRef}
      className={`card ${isDragging ? 'card-dragging' : ''} ${getPriorityClass(story.priority)}`}
      style={style}
      data-testid={`card-${story.id}`}
      onClick={onClick}
      {...listeners}
      {...attributes}
    >
      <div className="card-title">{story.title}</div>
      {story.description && (
        <div className="card-description">
          {story.description.substring(0, 100)}
          {story.description.length > 100 && '...'}
        </div>
      )}
      <div className="card-footer">
        <span className="story-id">#{story.id}</span>
        {story.worker_labels && story.worker_labels.length > 0 && (
          <div className="worker-labels">
            {story.worker_labels.slice(0, 3).map(label => (
              <span key={label} className="worker-label">{label}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Card;
