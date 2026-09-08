'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Network, Search, Filter, ShieldAlert, Sparkles, RefreshCw, ZoomIn, ZoomOut, Layers } from 'lucide-react';
import CytoscapeGraph from '@/components/CytoscapeGraph';
import NodeSelectionPanel from '@/components/NodeSelectionPanel';
import FilterSidebar, { FilterOptions } from '@/components/FilterSidebar';
import { cyberEngine, GraphData, GraphNode } from '@/lib/cybersaarthi_engine';

export default function NetworkGraphPage() {
  const searchParams = useSearchParams();
  const searchArg = searchParams.get('search') || '';

  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showFilterSidebar, setShowFilterSidebar] = useState(true);
  
  const [filters, setFilters] = useState<FilterOptions>({
    propertyTypes: ['PHONE', 'UPI', 'TRANSACTION_ID', 'URL', 'EMAIL', 'LOCATION'],
    location: '',
    category: '',
    minConnections: 1
  });

  // Load graph data based on search or full network
  useEffect(() => {
    let rawGraph: GraphData;
    if (searchArg) {
      // Find matching node
      const allIncidents = cyberEngine.getAllIncidents();
      const match = allIncidents.find(i => 
        i.id.toLowerCase() === searchArg.toLowerCase() ||
        i.properties.some(p => p.normalized_value.toLowerCase().includes(searchArg.toLowerCase()))
      );
      if (match) {
        rawGraph = cyberEngine.getIncidentGraph(match.id);
      } else {
        rawGraph = cyberEngine.getGlobalGraph(35);
      }
    } else {
      rawGraph = cyberEngine.getGlobalGraph(35);
    }

    // Apply Client Filters
    const filteredNodes = rawGraph.nodes.filter(node => {
      if (node.type !== 'Incident') {
        if (!filters.propertyTypes.includes(node.type)) return false;
      } else {
        if (filters.location && node.properties.location !== filters.location) return false;
        if (filters.category && node.properties.category !== filters.category) return false;
      }
      return true;
    });

    const validNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = rawGraph.edges.filter(e => validNodeIds.has(e.source) && validNodeIds.has(e.target));

    setGraphData({ nodes: filteredNodes, edges: filteredEdges });
  }, [searchArg, filters]);

  const handleResetFilters = () => {
    setFilters({
      propertyTypes: ['PHONE', 'UPI', 'TRANSACTION_ID', 'URL', 'EMAIL', 'LOCATION'],
      location: '',
      category: '',
      minConnections: 1
    });
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-65px)] overflow-hidden bg-obsidian-950">
      
      {/* Top Toolbar */}
      <div className="bg-obsidian-900/90 border-b border-obsidian-800 px-6 py-2.5 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-lg bg-cyber-cyan/15 text-cyber-cyan">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Knowledge Graph Explorer
              <span className="text-[10px] bg-cyber-purple/20 text-cyber-purple border border-cyber-purple/30 px-2 py-0.5 rounded font-semibold">
                Obsidian Network Engine
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">
              Showing <span className="text-cyber-cyan font-bold">{graphData.nodes.length}</span> nodes & <span className="text-amber-400 font-bold">{graphData.edges.length}</span> relationship edges
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          
          {/* Cluster lead warning badge */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Potential connected activity • Requires human validation</span>
          </div>

          <button
            onClick={() => setShowFilterSidebar(!showFilterSidebar)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              showFilterSidebar 
                ? 'bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/40' 
                : 'bg-obsidian-800 text-slate-300 border-obsidian-700'
            }`}
          >
            <Filter className="w-3.5 h-3.5" /> Filters
          </button>
        </div>
      </div>

      {/* Main Canvas Area with Sidebars */}
      <div className="flex-1 flex relative overflow-hidden">
        
        {/* Left Filter Drawer */}
        {showFilterSidebar && (
          <FilterSidebar
            filters={filters}
            onChangeFilters={setFilters}
            onReset={handleResetFilters}
          />
        )}

        {/* Center Cytoscape Canvas */}
        <div className="flex-1 relative h-full">
          <CytoscapeGraph
            graphData={graphData}
            onSelectNode={setSelectedNode}
            selectedNodeId={selectedNode?.id}
          />
        </div>

        {/* Right Node Selection Panel */}
        <NodeSelectionPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />

      </div>

    </div>
  );
}
