/**
 * Tests for UI-06: AgentStatus shows active agents with heartbeat indicator
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentStatus } from '../components/agent-status/AgentStatus';
import * as hooks from '../hooks/useKanboard';

// Mock the hooks
vi.mock('../hooks/useKanboard', () => ({
  useAgents: vi.fn()
}));

describe('AgentStatus - UI-06', () => {
  const mockRefresh = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(hooks.useAgents).mockReturnValue({
      agents: [
        {
          agent_id: 'claude-001',
          agent_type: 'claude',
          status: 'working',
          current_story: 123,
          last_heartbeat: Date.now() - 5000, // 5 seconds ago - healthy
          capabilities: ['code_generation', 'terminal_execution']
        },
        {
          agent_id: 'gemini-001',
          agent_type: 'gemini',
          status: 'idle',
          current_story: null,
          last_heartbeat: Date.now() - 10000, // 10 seconds ago - healthy
          capabilities: ['code_generation']
        },
        {
          agent_id: 'codex-001',
          agent_type: 'codex',
          status: 'validating',
          current_story: 456,
          last_heartbeat: Date.now() - 120000, // 2 minutes ago - stale
          capabilities: ['code_generation']
        }
      ],
      loading: false,
      refresh: mockRefresh
    });
  });

  it('renders agent status component', () => {
    render(<AgentStatus />);
    expect(screen.getByTestId('agent-status')).toBeInTheDocument();
  });

  it('shows AI Agents header', () => {
    render(<AgentStatus />);
    expect(screen.getByText('AI Agents')).toBeInTheDocument();
  });

  it('displays all agents', () => {
    render(<AgentStatus />);
    expect(screen.getByTestId('agent-claude-001')).toBeInTheDocument();
    expect(screen.getByTestId('agent-gemini-001')).toBeInTheDocument();
    expect(screen.getByTestId('agent-codex-001')).toBeInTheDocument();
  });

  it('shows agent type', () => {
    render(<AgentStatus />);
    expect(screen.getByText('claude')).toBeInTheDocument();
    expect(screen.getByText('gemini')).toBeInTheDocument();
    expect(screen.getByText('codex')).toBeInTheDocument();
  });

  it('shows agent status', () => {
    render(<AgentStatus />);
    expect(screen.getByText('working')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();
    expect(screen.getByText('validating')).toBeInTheDocument();
  });

  it('shows current story for working agents', () => {
    render(<AgentStatus />);
    expect(screen.getByText('Working on #123')).toBeInTheDocument();
    expect(screen.getByText('Working on #456')).toBeInTheDocument();
  });

  it('shows heartbeat indicator', () => {
    render(<AgentStatus />);
    expect(screen.getAllByTestId('heartbeat').length).toBeGreaterThan(0);
  });

  it('separates active and idle agents', () => {
    render(<AgentStatus />);
    expect(screen.getByText(/Active \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Idle \(1\)/)).toBeInTheDocument();
  });

  it('shows refresh button', () => {
    render(<AgentStatus />);
    const refreshButton = screen.getByText('↻');
    expect(refreshButton).toBeInTheDocument();
  });

  it('calls refresh on button click', () => {
    render(<AgentStatus />);
    fireEvent.click(screen.getByText('↻'));
    expect(mockRefresh).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useAgents).mockReturnValue({
      agents: [],
      loading: true,
      refresh: mockRefresh
    });

    render(<AgentStatus />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows no agents message when empty', () => {
    vi.mocked(hooks.useAgents).mockReturnValue({
      agents: [],
      loading: false,
      refresh: mockRefresh
    });

    render(<AgentStatus />);
    expect(screen.getByText('No agents registered')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<AgentStatus className="custom-class" />);
    expect(screen.getByTestId('agent-status')).toHaveClass('custom-class');
  });
});
