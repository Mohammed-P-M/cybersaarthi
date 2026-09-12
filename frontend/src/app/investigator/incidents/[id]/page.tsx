'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ShieldAlert, Network, FileText, MapPin, Calendar, CheckCircle2,
  ExternalLink, ChevronRight, Layers, Clock, AlertTriangle
} from 'lucide-react';
import CytoscapeGraph from '@/components/CytoscapeGraph';
import Timeline from '@/components/Timeline';
import type { GraphNode, GraphData } from '@/lib/cybersaarthi_engine';
import { getIncidentDetails, getIncidentGraph } from '@/lib/api';

export default function IncidentDetailPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const [incident,setIncident]=useState<any>(null);
  const [graphData,setGraphData]=useState<GraphData>({nodes:[],edges:[]});
  const [connectedIncidents,setConnectedIncidents]=useState<any[]>([]);
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null);
  const [activeTab, setActiveTab] = useState<'properties' | 'graph' | 'timeline'>('properties');

  useEffect(()=>{(async()=>{try{const [inc,raw]=await Promise.all([getIncidentDetails(incidentId),getIncidentGraph(incidentId)]);setIncident(inc);const typeMap:any={Phone:'PHONE',Transaction:'TRANSACTION_ID',Email:'EMAIL',Location:'LOCATION'};const nodes:GraphNode[]=raw.nodes.map((n:any)=>({id:n.id,label:n.label,type:typeMap[n.type]||n.type,properties:n.properties||{}}));setGraphData({nodes,edges:raw.edges.map((e:any)=>({id:e.id,source:e.source,target:e.target,rel_type:e.rel_type}))});const ids=new Set(nodes.filter(n=>n.type==='Incident'&&n.id!==incidentId).map(n=>n.id));const connected=await Promise.all(Array.from(ids).slice(0,20).map(id=>getIncidentDetails(id).catch(()=>null)));setConnectedIncidents(connected.filter(Boolean));}catch(e){console.error(e)}})()},[incidentId]);

  if (!incident) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <ShieldAlert className="w-12 h-12 text-rose-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-rose-400">Incident {incidentId} Not Found</h2>
        <Link href="/investigator" className="mt-4 inline-block text-cyber-cyan underline text-sm">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const dateStr = new Date(incident.timestamp).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'long', year: 'numeric'
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full space-y-6">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/investigator" className="hover:text-cyber-cyan transition">Dashboard</Link>
        <ChevronRight className="w-3 h-3" />
        <Link href="/investigator/network" className="hover:text-cyber-cyan transition">Network Graph</Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-cyber-cyan font-semibold">{incidentId}</span>
      </nav>

      {/* Incident Header Card */}
      <div className="glass-panel p-6 rounded-3xl border border-obsidian-800 flex flex-col md:flex-row items-start justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">{incidentId}</h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-lg bg-obsidian-800 text-amber-400 border border-obsidian-700">
                {incident.category}
              </span>
            </div>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">{incident.description}</p>

          <div className="flex flex-wrap gap-4 text-xs text-slate-400 pt-2">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-amber-400" /> {dateStr}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-pink-400" /> {incident.location}
            </span>
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyber-cyan" /> Source: {incident.source}
            </span>
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-emerald-400" /> {connectedIncidents.length} connected incidents
            </span>
          </div>
        </div>

        <Link
          href={`/investigator/network?search=${incidentId}`}
          className="shrink-0 py-3 px-5 rounded-2xl bg-gradient-to-r from-cyber-cyan to-cyber-blue text-obsidian-950 font-bold text-xs flex items-center gap-2 hover:opacity-90 transition shadow-lg shadow-cyber-cyan/20"
        >
          <Network className="w-4 h-4" /> Explore Full Network
        </Link>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 border-b border-obsidian-800 pb-0">
        {[
          { id: 'properties' as const, label: 'Extracted Properties', icon: CheckCircle2 },
          { id: 'graph' as const, label: 'Network Graph', icon: Network },
          { id: 'timeline' as const, label: 'Incident Timeline', icon: Clock }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-xs font-semibold border-b-2 transition ${
              activeTab === tab.id
                ? 'text-cyber-cyan border-cyber-cyan bg-cyber-cyan/5'
                : 'text-slate-400 border-transparent hover:text-slate-200'
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'properties' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Extracted Properties */}
          <div className="glass-panel p-6 rounded-3xl border border-obsidian-800 space-y-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Extracted Properties ({incident.properties.length})
            </h3>
            {incident.properties.map((prop) => {
              const stats = null;
              return (
                <div key={prop.id} className="p-3 rounded-xl bg-obsidian-900/80 border border-obsidian-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span className="text-[10px] font-bold uppercase text-cyber-cyan px-1.5 py-0.5 bg-cyber-cyan/10 rounded">
                        {prop.type}
                      </span>
                      <span className="font-mono text-xs text-slate-100 font-semibold break-all">{prop.normalized_value}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-obsidian-800 text-slate-300 border border-obsidian-700">
                        {(prop.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {stats && (
                    <p className="text-[11px] text-slate-400 mt-1 pl-5">
                      Observed in <span className="text-amber-400 font-bold">{stats.connectedIncidentsCount}</span> incidents
                      {stats.firstObserved !== 'N/A' && (
                        <> • First seen: <span className="text-slate-300">{stats.firstObserved}</span></>
                      )}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          {/* OCR Text + Connected Incidents */}
          <div className="space-y-6">
            {/* OCR Raw Output */}
            <div className="glass-panel p-6 rounded-3xl border border-obsidian-800">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-amber-400" /> OCR Extracted Text
              </h3>
              <div className="p-4 rounded-xl bg-obsidian-900/90 border border-obsidian-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                {incident.ocr_text || 'OCR text not available for synthetic records.'}
              </div>
            </div>

            {/* Connected Incidents */}
            <div className="glass-panel p-6 rounded-3xl border border-obsidian-800">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-3">
                <Network className="w-4 h-4 text-cyber-cyan" /> Connected Incidents ({connectedIncidents.length})
              </h3>

              {connectedIncidents.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {connectedIncidents.map(ci => (
                    <Link
                      key={ci.id}
                      href={`/investigator/incidents/${ci.id}`}
                      className="block p-3 rounded-xl bg-obsidian-900/80 border border-obsidian-800 hover:border-cyber-cyan/40 transition group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-rose-400">{ci.id}</span>
                        <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-cyber-cyan transition" />
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{ci.description}</p>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1 mt-1">
                        <MapPin className="w-3 h-3" /> {ci.location}
                      </span>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No directly connected incidents found.</p>
              )}

              {/* Investigative Lead Notice */}
              <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  This constitutes an <strong>investigative lead</strong> requiring human validation. Shared indicators do not conclusively prove criminal connection.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'graph' && (
        <div className="glass-panel rounded-3xl border border-obsidian-800 overflow-hidden" style={{ height: '550px' }}>
          <CytoscapeGraph
            graphData={graphData}
            onSelectNode={setSelectedGraphNode}
            selectedNodeId={selectedGraphNode?.id}
          />
        </div>
      )}

      {activeTab === 'timeline' && (
        <Timeline
          incidents={[incident, ...connectedIncidents]}
          selectedIncidentId={incidentId}
        />
      )}
    </div>
  );
}
