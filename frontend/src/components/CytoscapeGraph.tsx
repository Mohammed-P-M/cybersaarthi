'use client';

import React, { useEffect, useRef } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { GraphData, GraphNode } from '@/lib/cybersaarthi_engine';

if (typeof window !== 'undefined') {
  try {
    cytoscape.use(fcose);
  } catch (e) {
    // Already registered
  }
}

interface CytoscapeGraphProps {
  graphData: GraphData;
  onSelectNode: (node: GraphNode | null) => void;
  selectedNodeId?: string | null;
}

export default function CytoscapeGraph({ graphData, onSelectNode, selectedNodeId }: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Format elements for Cytoscape
    const elements: cytoscape.ElementDefinition[] = [];

    graphData.nodes.forEach(n => {
      const isIncident = n.type === 'Incident';
      const normVal = n.properties.normalized_value || n.properties.id || n.id;
      const displayLabel = isIncident ? n.id : `${n.type}: ${normVal}`;

      elements.push({
        data: {
          id: n.id,
          label: displayLabel,
          nodeType: n.type,
          rawNode: n
        }
      });
    });

    graphData.edges.forEach(e => {
      elements.push({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.rel_type
        }
      });
    });

    // Initialize Cytoscape Instance
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#cbd5e1',
            'font-size': '11px',
            'font-weight': '600',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-outline-color': '#07090e',
            'text-outline-width': 2,
            'width': 36,
            'height': 36,
            'border-width': 2,
            'border-color': '#334155',
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': 0.2
          }
        },
        {
          selector: 'node[nodeType = "Incident"]',
          style: {
            'shape': 'hexagon',
            'background-color': '#f43f5e',
            'border-color': '#fda4af',
            'width': 44,
            'height': 44
          }
        },
        {
          selector: 'node[nodeType = "UPI"]',
          style: {
            'shape': 'diamond',
            'background-color': '#8b5cf6',
            'border-color': '#c084fc',
            'width': 38,
            'height': 38
          }
        },
        {
          selector: 'node[nodeType = "PHONE"]',
          style: {
            'shape': 'rectangle',
            'background-color': '#06b6d4',
            'border-color': '#67e8f9',
            'width': 36,
            'height': 30
          }
        },
        {
          selector: 'node[nodeType = "TRANSACTION_ID"]',
          style: {
            'shape': 'round-rectangle',
            'background-color': '#10b981',
            'border-color': '#6ee7b7',
            'width': 40,
            'height': 32
          }
        },
        {
          selector: 'node[nodeType = "URL"]',
          style: {
            'shape': 'triangle',
            'background-color': '#f59e0b',
            'border-color': '#fde68a',
            'width': 38,
            'height': 38
          }
        },
        {
          selector: 'node[nodeType = "LOCATION"]',
          style: {
            'shape': 'pentagon',
            'background-color': '#ec4899',
            'border-color': '#fbcfe8',
            'width': 38,
            'height': 38
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#38bdf8',
            'width': 48,
            'height': 48
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.7
          }
        }
      ],
      layout: {
        name: 'fcose',
        animate: true,
        animationDuration: 500,
        randomize: false,
        fit: true,
        padding: 50,
        nodeRepulsion: 6500,
        idealEdgeLength: 100
      } as any
    });

    cyRef.current = cy;

    // Click node event listener
    cy.on('tap', 'node', (evt) => {
      const nodeSingular = evt.target as NodeSingular;
      const rawNode: GraphNode = nodeSingular.data('rawNode');
      onSelectNode(rawNode);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        onSelectNode(null);
      }
    });

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  // Center/highlight selected node if changed externally
  useEffect(() => {
    if (cyRef.current && selectedNodeId) {
      const nodeSingular = cyRef.current.getElementById(selectedNodeId);
      if (nodeSingular) {
        cyRef.current.nodes().unselect();
        nodeSingular.select();
        cyRef.current.animate({
          center: { eles: nodeSingular },
          zoom: 1.2
        }, { duration: 300 });
      }
    }
  }, [selectedNodeId]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} id="cy" className="w-full h-full min-h-[600px] rounded-2xl border border-obsidian-800 shadow-2xl" />
      
      {/* Legend Overlay */}
      <div className="absolute bottom-4 left-4 glass-panel p-3 rounded-xl flex flex-wrap gap-3 text-xs border border-obsidian-700/60 shadow-lg">
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-rose-500"></span> Incident</div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-purple-500 rotate-45"></span> UPI</div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 bg-cyan-500"></span> Phone</div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-emerald-500"></span> Transaction</div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 bg-amber-500"></span> URL</div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 bg-pink-500"></span> Location</div>
      </div>
    </div>
  );
}
