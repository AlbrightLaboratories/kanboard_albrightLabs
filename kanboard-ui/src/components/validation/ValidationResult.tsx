/**
 * ValidationResult Component
 *
 * Shows pass/fail with failure log.
 * Implements UI-07.
 */

import React from 'react';
import { useValidation } from '../../hooks/useKanboard';

export interface ValidationResultProps {
  storyId: number;
}

export function ValidationResult({ storyId }: ValidationResultProps) {
  const { result, loading } = useValidation(storyId);

  if (loading) {
    return <div className="validation-loading">Loading validation result...</div>;
  }

  if (!result) {
    return (
      <div className="validation-pending" data-testid="validation-pending">
        Validation not yet run
      </div>
    );
  }

  const isPassed = result.status === 'passed';
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div
      className={`validation-result ${isPassed ? 'passed' : 'failed'}`}
      data-testid="validation-result"
    >
      <div className="validation-header">
        <span className={`status-icon ${isPassed ? 'icon-passed' : 'icon-failed'}`}>
          {isPassed ? '✓' : '✗'}
        </span>
        <span className="status-text">
          Validation {isPassed ? 'Passed' : 'Failed'}
        </span>
      </div>

      <div className="validation-timestamp">
        Ran: {formatTime(result.timestamp)}
      </div>

      {!isPassed && result.failures && result.failures.length > 0 && (
        <div className="failure-log" data-testid="failure-log">
          <h4>Failures ({result.failures.length})</h4>
          <ul className="failure-list">
            {result.failures.map((failure, index) => (
              <li key={index} className="failure-item">
                <code>{failure}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ValidationResult;
