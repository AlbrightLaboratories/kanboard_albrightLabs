/**
 * StoryModal Component
 *
 * Full JIRA-like modal for story details.
 * Implements UI-03.
 */

import React, { useState, useEffect } from 'react';
import { Story, kanboardAPI } from '../../api/kanboard';

export interface StoryModalProps {
  story: Story;
  onClose: () => void;
  onUpdate?: (story: Story) => void;
}

export function StoryModal({ story, onClose, onUpdate }: StoryModalProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(story.title);
  const [description, setDescription] = useState(story.description);
  const [priority, setPriority] = useState(story.priority);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setTitle(story.title);
    setDescription(story.description);
    setPriority(story.priority);
  }, [story]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await kanboardAPI.updateStory(story.id, {
        title,
        description,
        priority
      });
      onUpdate?.({ ...story, title, description, priority });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const getPriorityLabel = (p: number) => {
    if (p >= 3) return 'High';
    if (p >= 2) return 'Medium';
    return 'Low';
  };

  return (
    <div className="modal-overlay" onClick={onClose} data-testid="story-modal">
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span className="story-id">#{story.id}</span>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {/* Title */}
          <div className="field">
            <label>Title</label>
            {editing ? (
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                data-testid="title-input"
              />
            ) : (
              <h2 data-testid="story-title">{story.title}</h2>
            )}
          </div>

          {/* Description / Acceptance Criteria */}
          <div className="field">
            <label>Description & Acceptance Criteria</label>
            {editing ? (
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={8}
                data-testid="description-input"
              />
            ) : (
              <div className="description" data-testid="story-description">
                {story.description || 'No description'}
              </div>
            )}
          </div>

          {/* Priority */}
          <div className="field">
            <label>Priority</label>
            {editing ? (
              <select
                value={priority}
                onChange={e => setPriority(Number(e.target.value))}
                data-testid="priority-select"
              >
                <option value={1}>Low</option>
                <option value={2}>Medium</option>
                <option value={3}>High</option>
              </select>
            ) : (
              <span
                className={`priority-badge priority-${getPriorityLabel(story.priority).toLowerCase()}`}
                data-testid="story-priority"
              >
                {getPriorityLabel(story.priority)}
              </span>
            )}
          </div>

          {/* Assignee */}
          <div className="field">
            <label>Assignee</label>
            <span data-testid="story-assignee">
              {story.owner_id ? `User #${story.owner_id}` : 'Unassigned'}
            </span>
          </div>

          {/* Worker Labels */}
          {story.worker_labels && story.worker_labels.length > 0 && (
            <div className="field">
              <label>Worker Labels</label>
              <div className="labels" data-testid="worker-labels">
                {story.worker_labels.map(label => (
                  <span key={label} className="label">{label}</span>
                ))}
              </div>
            </div>
          )}

          {/* Assigned Worker */}
          {story.assigned_worker && (
            <div className="field">
              <label>Assigned Worker</label>
              <span data-testid="assigned-worker">{story.assigned_worker}</span>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="save-button"
                data-testid="save-button"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setEditing(false)} className="cancel-button">
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="edit-button"
              data-testid="edit-button"
            >
              Edit
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default StoryModal;
