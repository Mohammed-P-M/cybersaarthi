'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Network, ChevronRight, ShieldAlert } from 'lucide-react';
import CytoscapeGraph from '@/components/CytoscapeGraph';
import NodeSelectionPanel from '@/components/NodeSelectionPanel';
import FilterSidebar, { FilterOptions } from '@/components/FilterSidebar';
import type { GraphNode, GraphData } from '@/lib/cybersaarthi_engine';
import { getIncidentGraph } from '@/lib/api';

export default function IncidentNetworkPage() {
  const params = useParams();
  const incidentId = params.incidentId as string;
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    propertyTypes: ['PHONE', 'UPI', 'TRANSACTION_ID', 'URL', 'EMAIL', 'LOCATION'],
    location: '',
    category: '',
    minConnections: 1
  });

  const [graphData,setGraphData]=useState<GraphData>({nodes:[],edges:[]});
  useEffect(()=>{getIncidentGraph(incidentId).then(raw=>{const typeMap:any={Phone:'PHONE',Transaction:'TRANSACTION_ID',Email:'EMAIL',Location:'LOCATION'}; const nodes:GraphNode[]=raw.nodes.map((n:any)=>({id:n.id,label:n.label,type:typeMap[n.type]||n.type,properties:n.properties||{}})); setGraphData({nodes,edges:raw.edges.map((e:any)=>({id:e.id,source:e.source,target:e.target,rel_type:e.rel_type}))});}).catch(console.error)},[incidentId]);
  const filteredGraphData=(()=>{const nodes=graphData.nodes.filter(n=>n.type==='Incident'||filters.propertyTypes.includes(n.type)); const ids=new Set(nodes.map(n=>n.id)); return {nodes,edges:graphData.edges.filter(e=>ids.has(e.source)&&ids.has(e.target))};})();

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-65px)] overflow-hidden bg-obsidian-950">

      {/* Toolbar */}
      <div className="bg-obsidian-900/90 border-b border-obsidian-800 px-6 py-2.5 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-1.5 text-xs text-slate-400">
            <Link href="/investigator" className="hover:text-cyber-cyan transition">Dashboard</Link>
            <ChevronRight className="w-3 h-3" />
            <Link href="/investigator/network" className="hover:text-cyber-cyan transition">Network</Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-cyber-cyan font-bold">{incidentId}</span>
          </nav>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400">
            <span className="text-cyber-cyan font-bold">{graphData.nodes.length}</span> nodes • 
            <span className="text-amber-400 font-bold ml-1">{graphData.edges.length}</span> edges
          </span>
        </div>
      </div>

      <div className="flex-1 flex relative overflow-hidden">
        {showFilters && (
          <FilterSidebar
            filters={filters}
            onChangeFilters={setFilters}
            onReset={() => setFilters({
              propertyTypes: ['PHONE', 'UPI', 'TRANSACTION_ID', 'URL', 'EMAIL', 'LOCATION'],
              location: '', category: '', minConnections: 1
            })}
          />
        )}

        <div className="flex-1 relative h-full">
          <CytoscapeGraph
            graphData={filteredGraphData}
            onSelectNode={setSelectedNode}
            selectedNodeId={selectedNode?.id}
          />
        </div>

        <NodeSelectionPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      </div>
    </div>
  );
}
