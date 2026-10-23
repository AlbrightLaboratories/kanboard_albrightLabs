/**
 * MobileBoard Component
 *
 * Mobile responsive board with swipe between columns.
 * Implements UI-10.
 */

import { useState, useRef, useEffect } from 'react';
import { useStories, useColumns } from '../../hooks/useKanboard';
import { Card } from './Card';
import { Story } from '../../api/kanboard';

export interface MobileBoardProps {
  projectId: number;
  onStoryClick?: (story: Story) => void;
}

export function MobileBoard({ projectId, onStoryClick }: MobileBoardProps) {
  const { stories, loading: storiesLoading } = useStories(projectId);
  const { columns, loading: columnsLoading } = useColumns(projectId);
  const [activeColumnIndex, setActiveColumnIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number>(0);
  const touchEndX = useRef<number>(0);

  const sortedColumns = [...columns].sort((a, b) => a.position - b.position);
  const activeColumn = sortedColumns[activeColumnIndex];

  const getStoriesForColumn = (columnId: number) => {
    return stories
      .filter(s => s.column_id === columnId)
      .sort((a, b) => a.position - b.position);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    const minSwipeDistance = 50;

    if (Math.abs(diff) > minSwipeDistance) {
      if (diff > 0 && activeColumnIndex < sortedColumns.length - 1) {
        // Swipe left - next column
        setActiveColumnIndex(prev => prev + 1);
      } else if (diff < 0 && activeColumnIndex > 0) {
        // Swipe right - previous column
        setActiveColumnIndex(prev => prev - 1);
      }
    }
  };

  const handleColumnSelect = (index: number) => {
    setActiveColumnIndex(index);
  };

  // Detect if mobile
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (storiesLoading || columnsLoading) {
    return <div className="mobile-board-loading">Loading...</div>;
  }

  if (!isMobile) {
    return null; // Only render on mobile
  }

  return (
    <div
      ref={containerRef}
      className="mobile-board"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      data-testid="mobile-board"
    >
      {/* Column tabs */}
      <div className="mobile-column-tabs" data-testid="column-tabs">
        {sortedColumns.map((column, index) => (
          <button
            key={column.id}
            className={`column-tab ${index === activeColumnIndex ? 'active' : ''}`}
            onClick={() => handleColumnSelect(index)}
            data-testid={`tab-${column.id}`}
          >
            {column.title}
            <span className="tab-count">
              ({getStoriesForColumn(column.id).length})
            </span>
          </button>
        ))}
      </div>

      {/* Swipe indicator */}
      <div className="swipe-indicator" data-testid="swipe-indicator">
        {sortedColumns.map((_, index) => (
          <span
            key={index}
            className={`indicator-dot ${index === activeColumnIndex ? 'active' : ''}`}
          />
        ))}
      </div>

      {/* Active column content */}
      {activeColumn && (
        <div className="mobile-column" data-testid={`mobile-column-${activeColumn.id}`}>
          <h3 className="column-title">{activeColumn.title}</h3>
          <div className="story-list">
            {getStoriesForColumn(activeColumn.id).map(story => (
              <Card
                key={story.id}
                story={story}
                onClick={() => onStoryClick?.(story)}
              />
            ))}
            {getStoriesForColumn(activeColumn.id).length === 0 && (
              <div className="empty-column">No stories</div>
            )}
          </div>
        </div>
      )}

      {/* Navigation hints */}
      <div className="swipe-hints">
        {activeColumnIndex > 0 && (
          <span className="hint-left" data-testid="swipe-hint-left">
            ← {sortedColumns[activeColumnIndex - 1]?.title}
          </span>
        )}
        {activeColumnIndex < sortedColumns.length - 1 && (
          <span className="hint-right" data-testid="swipe-hint-right">
            {sortedColumns[activeColumnIndex + 1]?.title} →
          </span>
        )}
      </div>
    </div>
  );
}

export default MobileBoard;
