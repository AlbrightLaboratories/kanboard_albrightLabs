import { useState } from 'react';
import { Board } from './components/board/Board';
import { AgentStatus } from './components/agent-status/AgentStatus';
import { WorkerList } from './components/workers/WorkerList';
import { useProjects } from './hooks/useKanboard';

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
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const { projects, loading, error } = useProjects();

  // Auto-select first project if none selected
  if (!selectedProjectId && projects.length > 0) {
    setSelectedProjectId(projects[0].id);
  }

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>
            <span style={{ color: colors.dashboard.accent }}>HR</span> Project Tracking
          </h1>
          {/* Project Selector */}
          {projects.length > 0 && (
            <select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
              style={{
                padding: '0.5rem',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                fontSize: '0.875rem',
              }}
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id} style={{ color: '#000' }}>
                  {project.name}
                </option>
              ))}
            </select>
          )}
        </div>
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
            Loading projects...
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: colors.status.failure }}>
            <p style={{ marginBottom: '1rem' }}>Failed to load projects</p>
            <p style={{ fontSize: '0.875rem', color: '#666' }}>{error}</p>
            <p style={{ fontSize: '0.875rem', marginTop: '1rem' }}>
              Make sure Kanboard is running at http://172.100.10.98:30088
            </p>
          </div>
        ) : activeTab === 'board' ? (
          selectedProjectId ? (
            <Board projectId={selectedProjectId} />
          ) : (
            <div style={{ textAlign: 'center', padding: '4rem' }}>
              No projects available. Create a project in Kanboard first.
            </div>
          )
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
        <span style={{ color: error ? colors.status.failure : colors.status.success }}>
          {error ? 'Disconnected' : 'Connected'}
        </span>
      </footer>
    </div>
  );
}
