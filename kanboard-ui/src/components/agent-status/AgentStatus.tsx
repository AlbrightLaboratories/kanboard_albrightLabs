/**
 * AgentStatus Component
 *
 * Shows active agents with heartbeat indicator.
 * Implements UI-06.
 */

// import React from 'react';
import { useAgents } from '../../hooks/useKanboard';
import { Agent } from '../../api/kanboard';

export interface AgentStatusProps {
  className?: string;
}

function AgentCard({ agent }: { agent: Agent }) {
  const isHealthy = Date.now() - agent.last_heartbeat < 60000; // 1 minute
  const statusColors: Record<string, string> = {
    idle: 'status-idle',
    working: 'status-working',
    validating: 'status-validating',
    blocked: 'status-blocked'
  };

  const formatTime = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  return (
    <div
      className={`agent-card ${statusColors[agent.status] || ''}`}
      data-testid={`agent-${agent.agent_id}`}
    >
      <div className="agent-header">
        <span className={`heartbeat-indicator ${isHealthy ? 'healthy' : 'stale'}`} />
        <span className="agent-type">{agent.agent_type}</span>
      </div>
      <div className="agent-id">{agent.agent_id}</div>
      <div className="agent-status">
        <span className="status-badge">{agent.status}</span>
        {agent.current_story && (
          <span className="current-story">Working on #{agent.current_story}</span>
        )}
      </div>
      <div className="agent-heartbeat" data-testid="heartbeat">
        Last seen: {formatTime(agent.last_heartbeat)}
      </div>
    </div>
  );
}

export function AgentStatus({ className }: AgentStatusProps) {
  const { agents, loading, error, refresh } = useAgents();

  if (loading) {
    return <div className="agent-status-loading">Loading agents...</div>;
  }

  if (error) {
    return (
      <div className={`agent-status ${className || ''}`} data-testid="agent-status">
        <div className="agent-status-header">
          <h3>AI Agents</h3>
          <button onClick={refresh} className="refresh-button">↻</button>
        </div>
        <div className="agent-status-notice" style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
          <p style={{ marginBottom: '1rem' }}>Backend not available</p>
          <p style={{ fontSize: '0.875rem' }}>The Maestro API is not deployed yet. Agents will appear here once the backend is running.</p>
        </div>
      </div>
    );
  }

  const activeAgents = agents.filter(a => a.status !== 'idle');
  const idleAgents = agents.filter(a => a.status === 'idle');

  return (
    <div className={`agent-status ${className || ''}`} data-testid="agent-status">
      <div className="agent-status-header">
        <h3>AI Agents</h3>
        <button onClick={refresh} className="refresh-button">↻</button>
      </div>

      {agents.length === 0 ? (
        <div className="no-agents">No agents registered</div>
      ) : (
        <>
          {activeAgents.length > 0 && (
            <div className="agent-section">
              <h4>Active ({activeAgents.length})</h4>
              <div className="agent-list">
                {activeAgents.map(agent => (
                  <AgentCard key={agent.agent_id} agent={agent} />
                ))}
              </div>
            </div>
          )}

          {idleAgents.length > 0 && (
            <div className="agent-section">
              <h4>Idle ({idleAgents.length})</h4>
              <div className="agent-list">
                {idleAgents.map(agent => (
                  <AgentCard key={agent.agent_id} agent={agent} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default AgentStatus;
