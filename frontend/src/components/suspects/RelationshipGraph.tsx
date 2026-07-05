import { useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { Suspect, RelationshipEdge } from '@/lib/api'

interface RelationshipGraphProps {
  suspects: Suspect[]
  edges: RelationshipEdge[]
  onSelectSuspect?: (name: string) => void
}

// Lay out nodes in a circle
function layoutNodes(suspects: Suspect[]): Node[] {
  const n = suspects.length
  const cx = 300, cy = 240, r = 180

  return suspects.map((s, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    const score = s.total_score

    return {
      id: s.name,
      position: { x, y },
      type: 'default',
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: { label: s.name, score },
      style: {
        backgroundColor: score > 70 ? 'rgba(140, 47, 43, 0.35)' :
                         score > 40 ? 'rgba(200, 149, 80, 0.18)' :
                         'rgba(27, 28, 34, 0.95)',
        border: score > 70 ? '1px solid var(--signal-red)' :
                score > 40 ? '1px solid var(--accent-amber-dim)' :
                '1px solid #2E2F36',
        borderRadius: '1px',
        color: 'var(--text-primary)',
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: '0.65rem',
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        padding: '8px 12px',
        width: 'auto',
        minWidth: '120px',
        textAlign: 'center',
      },
    }
  })
}

function buildEdges(edgeData: RelationshipEdge[]): Edge[] {
  return edgeData.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.relation_type.toUpperCase(),
    animated: false,
    style: {
      stroke: 'var(--accent-amber-dim)',
      strokeWidth: 1,
      strokeDasharray: '4 3',
    },
    labelStyle: {
      fill: 'var(--text-muted)',
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: '0.5rem',
      letterSpacing: '0.06em',
    },
    labelBgStyle: {
      fill: 'var(--bg-charcoal)',
      fillOpacity: 0.85,
    },
  }))
}

export function RelationshipGraph({ suspects, edges, onSelectSuspect }: RelationshipGraphProps) {
  const initialNodes = layoutNodes(suspects)
  const initialEdges = buildEdges(edges)

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edgeState, , onEdgesChange] = useEdgesState(initialEdges)

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onSelectSuspect?.(node.id)
    },
    [onSelectSuspect]
  )

  return (
    <div className="w-full h-full corkboard-surface" style={{ minHeight: '400px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edgeState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        attributionPosition="bottom-right"
        style={{ backgroundColor: 'transparent' }}
      >
        <Background
          color="rgba(200, 149, 80, 0.06)"
          gap={24}
          size={1}
        />
        <Controls
          style={{
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--divider)',
          }}
        />
        <MiniMap
          nodeColor={(node) => {
            const score = (node.data as { score: number }).score
            return score > 70 ? 'var(--signal-red)' :
                   score > 40 ? 'var(--accent-amber)' :
                   'var(--divider)'
          }}
          style={{
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--divider)',
          }}
        />
      </ReactFlow>
    </div>
  )
}
