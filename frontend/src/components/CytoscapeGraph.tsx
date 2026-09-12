'use client';

import React, { useEffect, useRef } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import { GraphData, GraphNode } from '@/lib/cybersaarthi_engine';

interface CytoscapeGraphProps {
  graphData: GraphData;
  onSelectNode: (node: GraphNode | null) => void;
  selectedNodeId?: string | null;
}

function starPositions(graphData: GraphData) {
  const degree = new Map<string, number>();
  graphData.nodes.forEach(n => degree.set(n.id, 0));
  graphData.edges.forEach(e => {
    degree.set(e.source, (degree.get(e.source) || 0) + 1);
    degree.set(e.target, (degree.get(e.target) || 0) + 1);
  });
  const hub = [...graphData.nodes].sort((a, b) => {
    const aScore = (degree.get(a.id) || 0) + (a.type === 'Incident' ? 0.1 : 0);
    const bScore = (degree.get(b.id) || 0) + (b.type === 'Incident' ? 0.1 : 0);
    return bScore - aScore;
  })[0]?.id;
  const positions: Record<string, { x: number; y: number }> = {};
  if (!hub) return positions;
  positions[hub] = { x: 0, y: 0 };

  const neighbors = new Set<string>();
  graphData.edges.forEach(e => {
    if (e.source === hub) neighbors.add(e.target);
    if (e.target === hub) neighbors.add(e.source);
  });
  const ring1 = [...neighbors].sort((a,b) => (degree.get(b)||0)-(degree.get(a)||0));
  const others = graphData.nodes.map(n => n.id).filter(id => id !== hub && !neighbors.has(id));

  const placeRing = (ids: string[], radius: number, startAngle: number) => {
    ids.forEach((id, i) => {
      const angle = startAngle + (i / Math.max(ids.length, 1)) * Math.PI * 2;
      positions[id] = { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
    });
  };
  placeRing(ring1, Math.max(240, 70 + ring1.length * 12), -Math.PI / 2);
  placeRing(others, Math.max(430, 130 + others.length * 7), -Math.PI / 2);
  return positions;
}

export default function CytoscapeGraph({ graphData, onSelectNode, selectedNodeId }: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const positions = starPositions(graphData);
    const elements: cytoscape.ElementDefinition[] = graphData.nodes.map(n => {
      const isIncident = n.type === 'Incident';
      const normVal = n.properties.normalized_value || n.properties.id || n.id;
      return {
        data: { id: n.id, label: isIncident ? n.id : `${n.type}: ${normVal}`, nodeType: n.type, rawNode: n },
        position: positions[n.id] || { x: 0, y: 0 }
      };
    });
    graphData.edges.forEach(e => elements.push({ data: { id: e.id, source: e.source, target: e.target, label: e.rel_type } }));

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        { selector: 'node', style: { label: 'data(label)', color: '#cbd5e1', 'font-size': '11px', 'font-weight': '600', 'text-valign': 'bottom', 'text-margin-y': 6, 'text-outline-color': '#07090e', 'text-outline-width': 2, width: 36, height: 36, 'border-width': 2, 'border-color': '#334155' } },
        { selector: 'node[nodeType = "Incident"]', style: { shape: 'hexagon', 'background-color': '#f43f5e', 'border-color': '#fda4af', width: 44, height: 44 } },
        { selector: 'node[nodeType = "UPI"]', style: { shape: 'diamond', 'background-color': '#8b5cf6', 'border-color': '#c084fc', width: 38, height: 38 } },
        { selector: 'node[nodeType = "PHONE"]', style: { shape: 'rectangle', 'background-color': '#06b6d4', 'border-color': '#67e8f9', width: 36, height: 30 } },
        { selector: 'node[nodeType = "TRANSACTION_ID"]', style: { shape: 'round-rectangle', 'background-color': '#10b981', 'border-color': '#6ee7b7', width: 40, height: 32 } },
        { selector: 'node[nodeType = "URL"]', style: { shape: 'triangle', 'background-color': '#f59e0b', 'border-color': '#fde68a', width: 38, height: 38 } },
        { selector: 'node[nodeType = "LOCATION"]', style: { shape: 'pentagon', 'background-color': '#ec4899', 'border-color': '#fbcfe8', width: 38, height: 38 } },
        { selector: 'node[nodeType = "CRIME_CATEGORY"]', style: { shape: 'round-rectangle', 'background-color': '#a855f7', 'border-color': '#d8b4fe', width: 42, height: 30 } },
        { selector: 'node:selected', style: { 'border-width': 4, 'border-color': '#38bdf8', width: 48, height: 48 } },
        { selector: 'edge', style: { width: 2, 'line-color': '#334155', 'target-arrow-color': '#475569', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', opacity: 0.7 } }
      ],
      layout: { name: 'preset', fit: true, padding: 70, animate: false }
    });
    cyRef.current = cy;
    cy.on('tap', 'node', evt => onSelectNode((evt.target as NodeSingular).data('rawNode')));
    cy.on('tap', evt => { if (evt.target === cy) onSelectNode(null); });
    return () => { cy.destroy(); };
  }, [graphData, onSelectNode]);

  useEffect(() => {
    if (cyRef.current && selectedNodeId) {
      const nodeSingular = cyRef.current.getElementById(selectedNodeId);
      if (nodeSingular) { cyRef.current.nodes().unselect(); nodeSingular.select(); cyRef.current.animate({ center: { eles: nodeSingular }, zoom: 1.2 }, { duration: 200 }); }
    }
  }, [selectedNodeId]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} id="cy" className="w-full h-full min-h-[600px] rounded-2xl border border-obsidian-800 shadow-2xl" />
      <div className="absolute bottom-4 left-4 glass-panel p-3 rounded-xl flex flex-wrap gap-3 text-xs border border-obsidian-700/60 shadow-lg">
        <div>Incident</div><div>UPI</div><div>Phone</div><div>Transaction</div><div>URL</div><div>Location</div><div>Crime category</div>
      </div>
    </div>
  );
}
