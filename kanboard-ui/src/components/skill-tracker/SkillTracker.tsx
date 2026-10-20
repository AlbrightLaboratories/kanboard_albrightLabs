/**
 * SkillTracker Component
 *
 * Shows skill progress and blocks manual Done move if incomplete.
 * Implements UI-04 and UI-05.
 */

import React from 'react';
import { useSkillProgress } from '../../hooks/useKanboard';

export interface SkillTrackerProps {
  storyId: number;
  onMoveRequest?: (canMove: boolean) => void;
}

const SKILL_ORDER = ['plan', 'design-a-prd', 'tdd', 'prove-it', 'release-it'];

export function SkillTracker({ storyId, onMoveRequest }: SkillTrackerProps) {
  const { progress, loading, canMoveToDone } = useSkillProgress(storyId);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return '✓';
      case 'failed': return '✗';
      case 'running': return '⟳';
      default: return '○';
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'passed': return 'skill-passed';
      case 'failed': return 'skill-failed';
      case 'running': return 'skill-running';
      default: return 'skill-pending';
    }
  };

  const handleMoveAttempt = () => {
    onMoveRequest?.(canMoveToDone);
  };

  if (loading) {
    return <div className="skill-tracker-loading">Loading skills...</div>;
  }

  if (!progress) {
    return null;
  }

  const completedCount = progress.skills.filter(s => s.status === 'passed').length;
  const totalCount = progress.skills.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="skill-tracker" data-testid="skill-tracker">
      <div className="skill-header">
        <h4>Skill Progress</h4>
        <span className="skill-progress-text">
          {completedCount}/{totalCount} ({progressPercent}%)
        </span>
      </div>

      <div className="skill-progress-bar">
        <div
          className="skill-progress-fill"
          style={{ width: `${progressPercent}%` }}
          data-testid="progress-bar"
        />
      </div>

      <div className="skill-list">
        {SKILL_ORDER.map(skillName => {
          const skill = progress.skills.find(s => s.name === skillName);
          const status = skill?.status || 'pending';

          return (
            <div
              key={skillName}
              className={`skill-item ${getStatusClass(status)}`}
              data-testid={`skill-${skillName}`}
            >
              <span className="skill-icon">{getStatusIcon(status)}</span>
              <span className="skill-name">/{skillName}</span>
              <span className="skill-status">{status}</span>
            </div>
          );
        })}
      </div>

      {!canMoveToDone && (
        <div className="skill-gate-warning" data-testid="skill-gate-warning">
          ⚠️ Cannot move to Done: Complete all skills first
        </div>
      )}

      <button
        className={`move-to-done-button ${canMoveToDone ? '' : 'disabled'}`}
        onClick={handleMoveAttempt}
        disabled={!canMoveToDone}
        data-testid="move-to-done-button"
      >
        {canMoveToDone ? 'Move to Done' : 'Skills Incomplete'}
      </button>
    </div>
  );
}

export default SkillTracker;
