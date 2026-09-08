'use client';

import React from 'react';
import Link from 'next/link';
import { Calendar, ShieldAlert, MapPin, ExternalLink } from 'lucide-react';
import { Incident } from '@/lib/cybersaarthi_engine';

interface TimelineProps {
  incidents: Incident[];
  selectedIncidentId?: string;
  onSelectIncident?: (id: string) => void;
}

export default function Timeline({ incidents, selectedIncidentId, onSelectIncident }: TimelineProps) {
  const sorted = [...incidents].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="glass-panel p-5 rounded-2xl border border-obsidian-800">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-5 h-5 text-amber-400" />
        <h3 className="text-base font-bold text-slate-100">Chronological Incident Timeline</h3>
      </div>

      <div className="relative border-l-2 border-obsidian-700 ml-4 space-y-6 py-2">
        {sorted.map((inc) => {
          const dateStr = new Date(inc.timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
          const isSelected = inc.id === selectedIncidentId;

          return (
            <div key={inc.id} className="relative pl-6 group">
              
              {/* Node Bullet */}
              <div className={`absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 transition-transform group-hover:scale-125 ${
                isSelected 
                  ? 'bg-cyber-cyan border-white shadow-lg shadow-cyber-cyan/50' 
                  : 'bg-obsidian-900 border-rose-500'
              }`} />

              {/* Event Card */}
              <div 
                onClick={() => onSelectIncident && onSelectIncident(inc.id)}
                className={`p-3.5 rounded-xl border transition cursor-pointer ${
                  isSelected 
                    ? 'bg-cyber-cyan/10 border-cyber-cyan/50 text-slate-100' 
                    : 'bg-obsidian-900/70 border-obsidian-800 hover:border-obsidian-700 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-rose-400 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5" /> {inc.id}
                  </span>
                  <span className="text-[11px] font-semibold text-slate-400 bg-obsidian-800 px-2 py-0.5 rounded">
                    {dateStr}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-1.5 line-clamp-2">{inc.description}</p>

                <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-obsidian-800 text-[11px]">
                  <span className="text-slate-400 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-pink-400" /> {inc.location}
                  </span>
                  <Link
                    href={`/investigator/incidents/${inc.id}`}
                    className="text-cyber-cyan font-semibold flex items-center gap-1 hover:underline"
                  >
                    Details <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}
