/**
 * WorkerList Component
 *
 * Shows all workers with health indicators.
 * Implements UI-11.
 */

import React from 'react';
import { useWorkers } from '../../hooks/useKanboard';
import { Worker } from '../../api/kanboard';

export interface WorkerListProps {
  onWorkerClick?: (worker: Worker) => void;
}

function WorkerCard({ worker, onClick }: { worker: Worker; onClick?: () => void }) {
  const isHealthy = Date.now() - worker.last_heartbeat < 60000;
  const statusColors: Record<string, string> = {
    active: 'status-active',
    idle: 'status-idle',
    busy: 'status-busy',
    offline: 'status-offline',
    error: 'status-error'
  };

  return (
    <div
      className={`worker-card ${statusColors[worker.status]}`}
      onClick={onClick}
      data-testid={`worker-${worker.worker_id}`}
    >
      <div className="worker-header">
        <span
          className={`health-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`}
          data-testid="health-indicator"
        />
        <span className="worker-name">{worker.name}</span>
      </div>
      <div className="worker-type">{worker.type}</div>
      <div className="worker-labels">
        {worker.labels.slice(0, 3).map(label => (
          <span key={label} className="label">{label}</span>
        ))}
        {worker.labels.length > 3 && (
          <span className="more-labels">+{worker.labels.length - 3}</span>
        )}
      </div>
      <div className="worker-status">
        <span className={`status-badge ${worker.status}`}>{worker.status}</span>
      </div>
      <div className="worker-capabilities">
        {worker.capabilities.slice(0, 2).map(cap => (
          <span key={cap} className="capability">{cap}</span>
        ))}
      </div>
    </div>
  );
}

export function WorkerList({ onWorkerClick }: WorkerListProps) {
  const { workers, loading, error, refresh } = useWorkers();

  if (loading) {
    return <div className="worker-list-loading">Loading workers...</div>;
  }

  if (error) {
    return (
      <div className="worker-list-error">
        Error: {error}
        <button onClick={refresh}>Retry</button>
      </div>
    );
  }

  const activeWorkers = workers.filter(w => w.status !== 'offline');
  const offlineWorkers = workers.filter(w => w.status === 'offline');

  return (
    <div className="worker-list" data-testid="worker-list">
      <div className="worker-list-header">
        <h3>LLM Workers</h3>
        <button onClick={refresh} className="refresh-button">↻</button>
      </div>

      {workers.length === 0 ? (
        <div className="no-workers">No workers registered</div>
      ) : (
        <>
          {activeWorkers.length > 0 && (
            <div className="worker-section">
              <h4>Online ({activeWorkers.length})</h4>
              <div className="worker-grid">
                {activeWorkers.map(worker => (
                  <WorkerCard
                    key={worker.worker_id}
                    worker={worker}
                    onClick={() => onWorkerClick?.(worker)}
                  />
                ))}
              </div>
            </div>
          )}

          {offlineWorkers.length > 0 && (
            <div className="worker-section offline">
              <h4>Offline ({offlineWorkers.length})</h4>
              <div className="worker-grid">
                {offlineWorkers.map(worker => (
                  <WorkerCard
                    key={worker.worker_id}
                    worker={worker}
                    onClick={() => onWorkerClick?.(worker)}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default WorkerList;
