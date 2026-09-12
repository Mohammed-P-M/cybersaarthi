'use client';

import React from 'react';
import Link from 'next/link';
import { X, Network, Calendar, ExternalLink, ShieldAlert, MapPin, Layers } from 'lucide-react';
import type { GraphNode } from '@/lib/cybersaarthi_engine';

interface NodeSelectionPanelProps {
  node: GraphNode | null;
  onClose: () => void;
  onExpandNetwork?: (nodeId: string) => void;
}

export default function NodeSelectionPanel({ node, onClose, onExpandNetwork }: NodeSelectionPanelProps) {
  if (!node) return null;
  const isIncident = node.type === 'Incident';
  const rawVal = node.properties.raw_value || node.properties.normalized_value || node.id;
  const normVal = node.properties.normalized_value || node.id;

  return (
    <aside className="w-80 lg:w-96 glass-panel border-l border-obsidian-700 h-full p-6 overflow-y-auto flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-obsidian-800">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-cyber-cyan/20 text-cyber-cyan">
              {isIncident ? <ShieldAlert className="w-5 h-5" /> : <Layers className="w-5 h-5" />}
            </span>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-cyber-cyan">{node.type} Node</span>
              <h3 className="text-base font-bold text-slate-100 break-all">{normVal}</h3>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-obsidian-800 transition"><X className="w-5 h-5" /></button>
        </div>

        {isIncident ? (
          <div className="mt-5 space-y-4 text-sm text-slate-300">
            <div><span className="text-xs text-slate-500 uppercase font-semibold">Incident ID</span><p className="font-mono text-cyan-400 font-semibold">{node.id}</p></div>
            <div><span className="text-xs text-slate-500 uppercase font-semibold">Category</span><p className="text-slate-200 font-medium">{node.properties.category || 'Not specified'}</p></div>
            <div><span className="text-xs text-slate-500 uppercase font-semibold">Reported Location</span><p className="text-slate-200 flex items-center gap-1.5 mt-0.5"><MapPin className="w-4 h-4 text-pink-400" /> {node.properties.location || 'Not specified'}</p></div>
            <div><span className="text-xs text-slate-500 uppercase font-semibold">Reported Date</span><p className="text-slate-200 flex items-center gap-1.5 mt-0.5"><Calendar className="w-4 h-4 text-amber-400" /> {node.properties.timestamp ? new Date(node.properties.timestamp).toLocaleDateString('en-GB') : 'Not specified'}</p></div>
            <div><span className="text-xs text-slate-500 uppercase font-semibold">Description</span><p className="text-slate-300 text-xs mt-1 bg-obsidian-900/80 p-3 rounded-lg border border-obsidian-800 leading-relaxed">{node.properties.description || 'No description provided.'}</p></div>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            <div className="bg-obsidian-900/90 p-3 rounded-xl border border-obsidian-800">
              <span className="text-xs text-slate-500 uppercase font-semibold">Normalized Value</span>
              <p className="font-mono text-cyber-cyan font-semibold text-sm break-all mt-1">{normVal}</p>
              {rawVal !== normVal && <p className="text-xs text-slate-400 mt-1">Raw: <span className="font-mono text-slate-300">{rawVal}</span></p>}
            </div>
            <p className="text-xs text-slate-500">Connection counts are calculated from the live graph/database. Select an incident to inspect its full network.</p>
          </div>
        )}
      </div>

      <div className="pt-6 border-t border-obsidian-800 space-y-2.5">
        {isIncident ? (
          <Link href={`/investigator/incidents/${node.id}`} className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-blue text-obsidian-950 font-bold text-sm flex items-center justify-center gap-2 hover:opacity-90 transition shadow-lg shadow-cyber-cyan/20"><ExternalLink className="w-4 h-4" /> View Full Incident Details</Link>
        ) : (
          <button onClick={() => onExpandNetwork?.(node.id)} className="w-full py-2.5 px-4 rounded-xl bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-cyber-cyan/30 transition"><Network className="w-4 h-4" /> Expand Network Graph</button>
        )}
      </div>
    </aside>
  );
}
