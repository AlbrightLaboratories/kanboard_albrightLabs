/**
 * ReworkButton Component
 *
 * Triggers rework flow for failed story.
 * Implements UI-08.
 */

import { useState } from 'react';
import { useValidation } from '../../hooks/useKanboard';

export interface ReworkButtonProps {
  storyId: number;
  onReworkStarted?: () => void;
}

export function ReworkButton({ storyId, onReworkStarted }: ReworkButtonProps) {
  const { result, triggerRework } = useValidation(storyId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Only show if validation failed
  if (!result || result.status === 'passed') {
    return null;
  }

  const handleRework = async () => {
    setLoading(true);
    setError(null);

    try {
      await triggerRework();
      onReworkStarted?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to trigger rework');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rework-container" data-testid="rework-container">
      <button
        onClick={handleRework}
        disabled={loading}
        className="rework-button"
        data-testid="rework-button"
      >
        {loading ? 'Starting rework...' : '🔄 Rework Story'}
      </button>

      {error && (
        <div className="rework-error" data-testid="rework-error">
          {error}
        </div>
      )}

      <p className="rework-hint">
        This will move the story back to In Progress for the agent to fix.
      </p>
    </div>
  );
}

export default ReworkButton;
