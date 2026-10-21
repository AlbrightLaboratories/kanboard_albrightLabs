import React, { useState, useEffect } from 'react';
import { Board } from './components/board/Board';
import { AgentStatus } from './components/agent-status/AgentStatus';
import { WorkerList } from './components/workers/WorkerList';

// Color scheme from PRD
const colors = {
  status: {
    failure: '#DC2626',    // Red - failure, money loss
    warning: '#F59E0B',    // Yellow - warning
    success: '#10B981',    // Green - success, money making
  },
  dashboard: {
    primary: '#2563EB',    // Blue
    background: '#FFFFFF', // White
    accent: '#D4AF37',     // Gold
    text: '#111827',       // Black
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState<'board' | 'agents' | 'workers'>('board');
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch projects from Kanboard API
    fetch('/api/projects')
      .then((res) => res.json())
      .then((data) => {
        setProjects(data.result || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.dashboard.background }}>
      {/* Header */}
      <header
        style={{
          backgroundColor: colors.dashboard.primary,
          color: 'white',
          padding: '1rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>
          <span style={{ color: colors.dashboard.accent }}>HR</span> Project Tracking
        </h1>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          {(['board', 'agents', 'workers'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                backgroundColor:
                  activeTab === tab ? colors.dashboard.accent : 'transparent',
                color: activeTab === tab ? colors.dashboard.text : 'white',
                fontWeight: activeTab === tab ? 600 : 400,
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ padding: '2rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem' }}>
            Loading...
          </div>
        ) : activeTab === 'board' ? (
          <Board />
        ) : activeTab === 'agents' ? (
          <AgentStatus />
        ) : (
          <WorkerList />
        )}
      </main>

      {/* Status Bar */}
      <footer
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: colors.dashboard.text,
          color: 'white',
          padding: '0.5rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.875rem',
        }}
      >
        <span>Kanboard AlbrightLabs v1.0.0</span>
        <span style={{ color: colors.status.success }}>Connected</span>
      </footer>
    </div>
  );
}
