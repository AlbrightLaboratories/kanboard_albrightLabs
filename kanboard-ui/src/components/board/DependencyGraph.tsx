/**
 * DependencyGraph Component
 *
 * Mini-map showing story relationships.
 * Implements UI-09.
 */

// import React from 'react';
import { useDependencyGraph } from '../../hooks/useKanboard';

export interface DependencyGraphProps {
  storyId: number;
  onClick?: (storyId: number) => void;
}

export function DependencyGraph({ storyId, onClick }: DependencyGraphProps) {
  const { graph, loading } = useDependencyGraph(storyId);

  if (loading) {
    return <div className="dependency-loading">Loading dependencies...</div>;
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="no-dependencies" data-testid="no-dependencies">
        No dependencies
      </div>
    );
  }

  // Calculate positions for nodes (simple layout)
  const nodePositions = new Map<number, { x: number; y: number }>();
  const mainNode = graph.nodes.find(n => n.id === storyId);
  const centerX = 150;
  const centerY = 100;

  if (mainNode) {
    nodePositions.set(mainNode.id, { x: centerX, y: centerY });
  }

  // Position blockers above, blocked below
  const blockers = graph.edges
    .filter(e => e.to === storyId && e.type === 'blocks')
    .map(e => e.from);
  const blocked = graph.edges
    .filter(e => e.from === storyId && e.type === 'blocks')
    .map(e => e.to);

  blockers.forEach((id, i) => {
    nodePositions.set(id, {
      x: centerX - 80 + (i * 60),
      y: centerY - 60
    });
  });

  blocked.forEach((id, i) => {
    nodePositions.set(id, {
      x: centerX - 80 + (i * 60),
      y: centerY + 60
    });
  });

  return (
    <div className="dependency-graph" data-testid="dependency-graph">
      <h4>Dependencies</h4>
      <svg width="300" height="200" className="graph-svg">
        {/* Draw edges */}
        {graph.edges.map((edge, i) => {
          const from = nodePositions.get(edge.from);
          const to = nodePositions.get(edge.to);
          if (!from || !to) return null;

          return (
            <line
              key={`edge-${i}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={edge.type === 'blocks' ? '#f44' : '#888'}
              strokeWidth={2}
              markerEnd="url(#arrowhead)"
              data-testid={`edge-${edge.from}-${edge.to}`}
            />
          );
        })}

        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#888" />
          </marker>
        </defs>

        {/* Draw nodes */}
        {graph.nodes.map(node => {
          const pos = nodePositions.get(node.id);
          if (!pos) return null;

          const isMain = node.id === storyId;

          return (
            <g
              key={node.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              onClick={() => onClick?.(node.id)}
              style={{ cursor: onClick ? 'pointer' : 'default' }}
              data-testid={`node-${node.id}`}
            >
              <circle
                r={isMain ? 25 : 20}
                fill={isMain ? '#4a90d9' : '#6c757d'}
                stroke={isMain ? '#2a70b9' : '#5c656d'}
                strokeWidth={2}
              />
              <text
                textAnchor="middle"
                dy="0.3em"
                fill="white"
                fontSize={isMain ? 12 : 10}
              >
                #{node.id}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="dependency-legend">
        <span className="legend-item">
          <span className="legend-color blocker" /> Blockers
        </span>
        <span className="legend-item">
          <span className="legend-color blocked" /> Blocked
        </span>
      </div>
    </div>
  );
}

export default DependencyGraph;
