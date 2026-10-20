/**
 * StoryWorkerPicker Component
 *
 * Allows setting worker labels on a story.
 * Implements UI-13.
 */

import React, { useState, useEffect } from 'react';
import { useWorkers } from '../../hooks/useKanboard';
import { kanboardAPI, Story } from '../../api/kanboard';

export interface StoryWorkerPickerProps {
  story: Story;
  onUpdate?: (labels: string[]) => void;
}

// Common labels that can be selected
const COMMON_LABELS = [
  'python',
  'typescript',
  'javascript',
  'rust',
  'go',
  'frontend',
  'backend',
  'devops',
  'ml',
  'gpu-required',
  'high-memory',
  'fast'
];

export function StoryWorkerPicker({ story, onUpdate }: StoryWorkerPickerProps) {
  const { workers } = useWorkers();
  const [selectedLabels, setSelectedLabels] = useState<string[]>(
    story.worker_labels || []
  );
  const [customLabel, setCustomLabel] = useState('');
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setSelectedLabels(story.worker_labels || []);
  }, [story.worker_labels]);

  // Get unique labels from all workers
  const workerLabels = [...new Set(workers.flatMap(w => w.labels))];
  const allLabels = [...new Set([...COMMON_LABELS, ...workerLabels])];

  const toggleLabel = (label: string) => {
    setDirty(true);
    setSelectedLabels(prev =>
      prev.includes(label)
        ? prev.filter(l => l !== label)
        : [...prev, label]
    );
  };

  const addCustomLabel = () => {
    const label = customLabel.trim().toLowerCase();
    if (label && !selectedLabels.includes(label)) {
      setDirty(true);
      setSelectedLabels(prev => [...prev, label]);
      setCustomLabel('');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await kanboardAPI.updateWorkerLabels(story.id, selectedLabels);
      onUpdate?.(selectedLabels);
      setDirty(false);
    } finally {
      setSaving(false);
    }
  };

  // Find matching workers for current labels
  const matchingWorkers = workers.filter(w =>
    selectedLabels.some(label => w.labels.includes(label))
  );

  return (
    <div className="story-worker-picker" data-testid="story-worker-picker">
      <h4>Worker Labels</h4>
      <p className="picker-hint">
        Select labels to route this story to workers with matching capabilities.
      </p>

      {/* Current selections */}
      <div className="selected-labels" data-testid="selected-labels">
        {selectedLabels.map(label => (
          <span
            key={label}
            className="selected-label"
            onClick={() => toggleLabel(label)}
          >
            {label} ×
          </span>
        ))}
        {selectedLabels.length === 0 && (
          <span className="no-labels">No labels selected (any worker can handle)</span>
        )}
      </div>

      {/* Available labels */}
      <div className="available-labels">
        <h5>Available Labels</h5>
        <div className="label-grid" data-testid="label-grid">
          {allLabels.map(label => (
            <button
              key={label}
              className={`label-button ${selectedLabels.includes(label) ? 'selected' : ''}`}
              onClick={() => toggleLabel(label)}
              data-testid={`label-${label}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Custom label input */}
      <div className="custom-label">
        <input
          type="text"
          value={customLabel}
          onChange={e => setCustomLabel(e.target.value)}
          placeholder="Add custom label..."
          onKeyDown={e => e.key === 'Enter' && addCustomLabel()}
          data-testid="custom-label-input"
        />
        <button onClick={addCustomLabel} data-testid="add-label-button">
          Add
        </button>
      </div>

      {/* Matching workers preview */}
      {selectedLabels.length > 0 && (
        <div className="matching-workers" data-testid="matching-workers">
          <h5>Matching Workers ({matchingWorkers.length})</h5>
          {matchingWorkers.length > 0 ? (
            <ul>
              {matchingWorkers.slice(0, 5).map(w => (
                <li key={w.worker_id}>
                  {w.name} ({w.type})
                </li>
              ))}
              {matchingWorkers.length > 5 && (
                <li>... and {matchingWorkers.length - 5} more</li>
              )}
            </ul>
          ) : (
            <p className="no-matches">No workers match these labels</p>
          )}
        </div>
      )}

      {/* Save button */}
      {dirty && (
        <button
          onClick={handleSave}
          disabled={saving}
          className="save-button"
          data-testid="save-labels-button"
        >
          {saving ? 'Saving...' : 'Save Labels'}
        </button>
      )}
    </div>
  );
}

export default StoryWorkerPicker;
