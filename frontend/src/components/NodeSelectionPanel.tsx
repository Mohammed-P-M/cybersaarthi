'use client';

import React from 'react';
import Link from 'next/link';
import { X, Network, Calendar, ExternalLink, ShieldAlert, Phone, Globe, MapPin, Hash, Layers } from 'lucide-react';
import { GraphNode, cyberEngine } from '@/lib/cybersaarthi_engine';

interface NodeSelectionPanelProps {
  node: GraphNode | null;
  onClose: () => void;
  onExpandNetwork?: (nodeId: string) => void;
  onViewTimeline?: (nodeId: string) => void;
}

export default function NodeSelectionPanel({ node, onClose, onExpandNetwork, onViewTimeline }: NodeSelectionPanelProps) {
  if (!node) return null;

  const isIncident = node.type === 'Incident';
  const propId = node.id;
  const stats = !isIncident ? cyberEngine.getPropertyStats(propId) : null;

  const rawVal = node.properties.raw_value || node.properties.normalized_value || node.id;
  const normVal = node.properties.normalized_value || node.id;

  return (
    <aside className="w-80 lg:w-96 glass-panel border-l border-obsidian-700 h-full p-6 overflow-y-auto flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
      
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-obsidian-800">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-cyber-cyan/20 text-cyber-cyan">
              {isIncident ? <ShieldAlert className="w-5 h-5" /> : <Layers className="w-5 h-5" />}
            </span>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-cyber-cyan">
                {node.type} Node
              </span>
              <h3 className="text-base font-bold text-slate-100 break-all">{normVal}</h3>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-obsidian-800 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content details */}
        {isIncident ? (
          <div className="mt-5 space-y-4 text-sm text-slate-300">
            <div>
              <span className="text-xs text-slate-500 uppercase font-semibold">Incident ID</span>
              <p className="font-mono text-cyan-400 font-semibold">{node.id}</p>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase font-semibold">Category</span>
              <p className="text-slate-200 font-medium">{node.properties.category || 'CYBER_FRAUD'}</p>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase font-semibold">Reported Location</span>
              <p className="text-slate-200 flex items-center gap-1.5 mt-0.5">
                <MapPin className="w-4 h-4 text-pink-400" /> {node.properties.location || 'Kochi'}
              </p>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase font-semibold">Reported Date</span>
              <p className="text-slate-200 flex items-center gap-1.5 mt-0.5">
                <Calendar className="w-4 h-4 text-amber-400" /> {node.properties.timestamp ? new Date(node.properties.timestamp).toLocaleDateString('en-GB') : '2026-08-01'}
              </p>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase font-semibold">Description</span>
              <p className="text-slate-300 text-xs mt-1 bg-obsidian-900/80 p-3 rounded-lg border border-obsidian-800 leading-relaxed">
                {node.properties.description}
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            
            {/* Value Display */}
            <div className="bg-obsidian-900/90 p-3 rounded-xl border border-obsidian-800">
              <span className="text-xs text-slate-500 uppercase font-semibold">Normalized Indicator</span>
              <p className="font-mono text-cyber-cyan font-semibold text-sm break-all mt-1">{normVal}</p>
              {rawVal !== normVal && (
                <p className="text-xs text-slate-400 mt-1">Raw: <span className="font-mono text-slate-300">{rawVal}</span></p>
              )}
            </div>

            {/* Network Connections metrics */}
            {stats && (
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="bg-obsidian-900/60 p-3 rounded-xl border border-obsidian-800">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> Connected Incidents
                  </div>
                  <span className="text-xl font-extrabold text-rose-400 mt-1 block">{stats.connectedIncidentsCount}</span>
                </div>

                <div className="bg-obsidian-900/60 p-3 rounded-xl border border-obsidian-800">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Phone className="w-3.5 h-3.5 text-cyan-400" /> Linked Phones
                  </div>
                  <span className="text-xl font-extrabold text-cyan-400 mt-1 block">{stats.connectedPhonesCount}</span>
                </div>

                <div className="bg-obsidian-900/60 p-3 rounded-xl border border-obsidian-800">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Globe className="w-3.5 h-3.5 text-amber-400" /> Linked URLs
                  </div>
                  <span className="text-xl font-extrabold text-amber-400 mt-1 block">{stats.connectedUrlsCount}</span>
                </div>

                <div className="bg-obsidian-900/60 p-3 rounded-xl border border-obsidian-800">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-pink-400" /> Locations
                  </div>
                  <span className="text-xl font-extrabold text-pink-400 mt-1 block">{stats.connectedLocationsCount}</span>
                </div>
              </div>
            )}

            {/* Timeline range */}
            {stats && (
              <div className="space-y-2 pt-2 border-t border-obsidian-800 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>First observed:</span>
                  <span className="text-slate-200 font-medium">{stats.firstObserved}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last observed:</span>
                  <span className="text-slate-200 font-medium">{stats.lastObserved}</span>
                </div>
              </div>
            )}

          </div>
        )}

      </div>

      {/* Action Buttons */}
      <div className="pt-6 border-t border-obsidian-800 space-y-2.5">
        {isIncident ? (
          <Link
            href={`/investigator/incidents/${node.id}`}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-blue text-obsidian-950 font-bold text-sm flex items-center justify-center gap-2 hover:opacity-90 transition shadow-lg shadow-cyber-cyan/20"
          >
            <ExternalLink className="w-4 h-4" /> View Full Incident Details
          </Link>
        ) : (
          <>
            <button
              onClick={() => onExpandNetwork && onExpandNetwork(node.id)}
              className="w-full py-2.5 px-4 rounded-xl bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-cyber-cyan/30 transition"
            >
              <Network className="w-4 h-4" /> Expand Network Graph
            </button>
            
            {stats && stats.connectedIncidents.length > 0 && (
              <Link
                href={`/investigator/incidents/${stats.connectedIncidents[0].id}`}
                className="w-full py-2 px-4 rounded-xl bg-obsidian-800 text-slate-200 font-medium text-xs flex items-center justify-center gap-2 hover:bg-obsidian-700 transition"
              >
                <ExternalLink className="w-3.5 h-3.5" /> View Connected Incidents ({stats.connectedIncidentsCount})
              </Link>
            )}
          </>
        )}
      </div>

    </aside>
  );
}
