// File: src/TraceGraph.tsx
import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { TraceDetail } from "./api";

interface TraceGraphProps {
  trace: TraceDetail;
}

const HOP_SPACING_X = 240;
const NODE_SPACING_Y = 110;

function nodeColor(node: TraceDetail["nodes"][number]): string {
  if (node.is_sanctioned) return "#E24B4A"; // sinalizado
  if (node.is_known_exchange) return "#378ADD"; // exchange conhecida
  if (node.is_target) return "#D85A30"; // endereço investigado
  if (node.is_likely_hub) return "#A855F7"; // hub de alto fan-out (não expandido)
  return "#4B5563"; // sem rótulo (gray-600)
}

function shortAddr(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export default function TraceGraph({ trace }: TraceGraphProps) {
  const { nodes, edges } = useMemo(() => {
    // Agrupa endereços por profundidade pra montar o layout em colunas
    // (esquerda = origem, direita = mais saltos) — sem precisar de uma lib
    // de auto-layout, já que a profundidade já vem pronta da API.
    const byDepth = new Map<number, TraceDetail["nodes"]>();
    for (const n of trace.nodes) {
      const list = byDepth.get(n.depth) ?? [];
      list.push(n);
      byDepth.set(n.depth, list);
    }

    const flowNodes: Node[] = [];
    for (const [depth, group] of byDepth.entries()) {
      group.forEach((n, i) => {
        const yOffset = (group.length - 1) * NODE_SPACING_Y * 0.5;
        flowNodes.push({
          id: n.address,
          position: { x: depth * HOP_SPACING_X, y: i * NODE_SPACING_Y - yOffset },
          data: {
            label: (
              <div className="text-center">
                <div className="font-mono text-xs">{shortAddr(n.address)}</div>
                {n.is_target && <div className="text-[10px] opacity-80">investigado</div>}
                {n.is_sanctioned && <div className="text-[10px] opacity-80">sancionado</div>}
                {n.is_known_exchange && <div className="text-[10px] opacity-80">exchange</div>}
                {n.is_likely_hub && <div className="text-[10px] opacity-80">hub (não expandido)</div>}
                {n.label && <div className="text-[10px] opacity-80">{n.label}</div>}
              </div>
            ),
          },
          style: {
            background: nodeColor(n),
            color: "white",
            border: "1px solid rgba(255,255,255,0.2)",
            borderRadius: 8,
            padding: 8,
            width: 150,
          },
        });
      });
    }

    const nodeIds = new Set(flowNodes.map((n) => n.id));
    const flowEdges: Edge[] = trace.edges
      .filter((e) => nodeIds.has(e.from) && nodeIds.has(e.to))
      .map((e, i) => ({
        id: `${e.tx_hash}-${i}`,
        source: e.from,
        target: e.to,
        label: `${e.amount.toFixed(e.token_symbol ? 2 : 4)} ${e.token_symbol ?? "ETH"}`,
        animated: true,
        style: { stroke: "#6B7280" },
        labelStyle: { fill: "#D1D5DB", fontSize: 11 },
        labelBgStyle: { fill: "#111827" },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#6B7280" },
      }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [trace]);

  return (
    <div className="w-full h-[480px] rounded border border-gray-700 bg-gray-950">
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
        <Background color="#374151" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
