/**
 * WorkerAssignment Component
 *
 * Shows current worker and allows reassignment.
 * Implements UI-14.
 */

import { useState } from 'react';
import { useWorkers } from '../../hooks/useKanboard';
import { kanboardAPI, Story, Worker } from '../../api/kanboard';

export interface WorkerAssignmentProps {
  story: Story;
  onAssigned?: (workerId: string) => void;
}

export function WorkerAssignment({ story, onAssigned }: WorkerAssignmentProps) {
  const { workers } = useWorkers();
  const [showPicker, setShowPicker] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentWorker = workers.find(w => w.worker_id === story.assigned_worker);

  // Filter workers that match story labels (or all if no labels)
  const availableWorkers = story.worker_labels && story.worker_labels.length > 0
    ? workers.filter(w =>
        w.status !== 'offline' &&
        story.worker_labels!.some(label => w.labels.includes(label))
      )
    : workers.filter(w => w.status !== 'offline');

  const handleAssign = async (worker: Worker) => {
    setAssigning(true);
    setError(null);

    try {
      await kanboardAPI.assignWorker(story.id, worker.worker_id);
      onAssigned?.(worker.worker_id);
      setShowPicker(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to assign worker');
    } finally {
      setAssigning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: 'badge-active',
      idle: 'badge-idle',
      busy: 'badge-busy'
    };
    return colors[status] || 'badge-default';
  };

  return (
    <div className="worker-assignment" data-testid="worker-assignment">
      <h4>Assigned Worker</h4>

      {currentWorker ? (
        <div className="current-worker" data-testid="current-worker">
          <div className="worker-info">
            <span className="worker-name">{currentWorker.name}</span>
            <span className="worker-type">({currentWorker.type})</span>
            <span className={`status-badge ${getStatusBadge(currentWorker.status)}`}>
              {currentWorker.status}
            </span>
          </div>
          <button
            onClick={() => setShowPicker(true)}
            className="reassign-button"
            data-testid="reassign-button"
          >
            Reassign
          </button>
        </div>
      ) : (
        <div className="no-worker" data-testid="no-worker">
          <span>No worker assigned</span>
          <button
            onClick={() => setShowPicker(true)}
            className="assign-button"
            data-testid="assign-button"
          >
            Assign Worker
          </button>
        </div>
      )}

      {showPicker && (
        <div className="worker-picker" data-testid="worker-picker">
          <div className="picker-header">
            <h5>Select Worker</h5>
            <button
              onClick={() => setShowPicker(false)}
              className="close-picker"
            >
              ×
            </button>
          </div>

          {availableWorkers.length === 0 ? (
            <div className="no-workers-available">
              No workers available for this story's labels
            </div>
          ) : (
            <div className="worker-options">
              {availableWorkers.map(worker => (
                <div
                  key={worker.worker_id}
                  className={`worker-option ${worker.worker_id === story.assigned_worker ? 'current' : ''}`}
                  onClick={() => !assigning && handleAssign(worker)}
                  data-testid={`worker-option-${worker.worker_id}`}
                >
                  <div className="option-info">
                    <span className="option-name">{worker.name}</span>
                    <span className="option-type">{worker.type}</span>
                  </div>
                  <div className="option-labels">
                    {worker.labels.slice(0, 3).map(label => (
                      <span key={label} className="label">{label}</span>
                    ))}
                  </div>
                  <span className={`status-badge ${getStatusBadge(worker.status)}`}>
                    {worker.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="assignment-error" data-testid="assignment-error">
              {error}
            </div>
          )}

          {assigning && (
            <div className="assigning-indicator">Assigning...</div>
          )}
        </div>
      )}
    </div>
  );
}

export default WorkerAssignment;
