'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { CheckCircle2, ShieldAlert, Network, ArrowRight, FileText, Database, MapPin } from 'lucide-react';
import { cyberEngine } from '@/lib/cybersaarthi_engine';

export default function ResultPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const incident = cyberEngine.getIncident(incidentId);

  if (!incident) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <h2 className="text-xl font-bold text-rose-400">Incident Not Found</h2>
        <Link href="/" className="mt-4 inline-block text-cyber-cyan underline text-sm">Return to Submission Portal</Link>
      </div>
    );
  }

  // Calculate historical database matches
  const matchCounts: Record<string, number> = {};
  incident.properties.forEach(p => {
    const stats = cyberEngine.getPropertyStats(`${p.type}:${p.normalized_value}`);
    matchCounts[p.normalized_value] = stats ? stats.connectedIncidentsCount : 1;
  });

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 w-full space-y-8">
      
      {/* Success Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-emerald-500/30 bg-emerald-500/10 flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold text-emerald-400 tracking-wider">Analysis Complete</span>
            <h1 className="text-2xl font-extrabold text-white mt-1">
              Evidence Processed & Graph Connected
            </h1>
            <p className="text-slate-300 text-xs mt-1">
              Incident ID: <span className="font-mono font-bold text-cyber-cyan">{incident.id}</span> • Source: {incident.source}
            </p>
          </div>
        </div>

        <Link
          href={`/investigator/network/${incident.id}`}
          className="py-3 px-5 rounded-2xl bg-gradient-to-r from-cyber-cyan to-cyber-blue text-obsidian-950 font-bold text-xs tracking-wide flex items-center gap-2 hover:opacity-90 transition shadow-lg shadow-cyber-cyan/20"
        >
          <Network className="w-4 h-4" /> View Connections Graph <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Detected Extracted Properties */}
        <div className="glass-panel p-6 rounded-3xl border border-obsidian-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-obsidian-800 pb-3">
            <Database className="w-5 h-5 text-cyber-cyan" />
            <h3 className="text-base font-bold text-slate-100">Extracted Indicators & Confidence</h3>
          </div>

          <div className="space-y-2.5">
            {incident.properties.map((prop) => {
              const matches = matchCounts[prop.normalized_value] || 1;
              return (
                <div key={prop.id} className="p-3.5 rounded-2xl bg-obsidian-900/80 border border-obsidian-800 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-bold uppercase text-cyber-cyan">{prop.type}:</span>
                      <span className="font-mono text-xs text-slate-100 font-semibold">{prop.normalized_value}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 pl-6">
                      Historical Matches: <span className="text-amber-400 font-bold">{matches} incidents</span>
                    </p>
                  </div>

                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-obsidian-800 text-slate-300 border border-obsidian-700">
                    Conf: {(prop.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* OCR Raw Text & Insights */}
        <div className="glass-panel p-6 rounded-3xl border border-obsidian-800 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b border-obsidian-800 pb-3">
              <FileText className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-slate-100">PaddleOCR Extracted Text</h3>
            </div>

            <div className="mt-4 p-4 rounded-2xl bg-obsidian-900/90 border border-obsidian-800 font-mono text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto">
              {incident.ocr_text || "Payment of ₹800 successful to scammer123@upi."}
            </div>
          </div>

          {/* Historical Cluster Alert */}
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-amber-400">
              <ShieldAlert className="w-4 h-4" /> Potential Connected Activity Identified
            </div>
            <p className="text-[11px] text-slate-300">
              Indicators in this report share matches with existing synthetic intelligence clusters (e.g. scammer123@upi).
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}
