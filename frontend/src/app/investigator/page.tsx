'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, ShieldAlert, Network, Layers, MapPin, ExternalLink, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { getDashboardStats } from '@/lib/api';

export default function InvestigatorDashboard() {
  const [stats,setStats]=useState<any>(null);
  useEffect(()=>{getDashboardStats().then(setStats).catch(console.error)},[]);
  if(!stats)return <div className="max-w-7xl mx-auto px-6 py-12 text-slate-400">Loading intelligence dashboard...</div>;

  const chartData = (stats.top_connected_properties || []).map((p:any) => ({
    name: p.normalized_value.length > 14 ? p.normalized_value.substring(0, 12) + '...' : p.normalized_value,
    count: p.connected_incidents_count,
    type: p.type
  }));

  const COLORS = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 w-full space-y-8">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-obsidian-800 pb-6">
        <div>
          <span className="text-xs uppercase font-bold text-cyber-cyan tracking-wider">Investigator Portal</span>
          <h1 className="text-2xl font-extrabold text-white">Cybercrime Intelligence Dashboard</h1>
          <p className="text-slate-400 text-xs mt-1">Cross-incident relationship discovery & indicator degree analytics</p>
        </div>

        <Link
          href="/investigator/network"
          className="py-2.5 px-5 rounded-2xl bg-gradient-to-r from-cyber-cyan to-cyber-blue text-obsidian-950 font-bold text-xs flex items-center gap-2 hover:opacity-90 transition shadow-lg shadow-cyber-cyan/20"
        >
          <Network className="w-4 h-4" /> Open Full Knowledge Graph
        </Link>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="glass-panel p-5 rounded-2xl border border-obsidian-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Incidents</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <span className="text-3xl font-extrabold text-white mt-2 block">{stats.total_incidents}</span>
          <span className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3" /> {stats.new_incidents_today || 0} citizen reports
          </span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-obsidian-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Unique Properties</span>
            <Layers className="w-4 h-4 text-cyber-cyan" />
          </div>
          <span className="text-3xl font-extrabold text-white mt-2 block">{stats.unique_properties}</span>
          <span className="text-[11px] text-slate-400 mt-1 block">UPI, Phone, URL, Transaction</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-obsidian-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Shared Indicator Hubs</span>
            <Network className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-3xl font-extrabold text-amber-400 mt-2 block">{stats.connected_clusters}</span>
          <span className="text-[11px] text-slate-400 mt-1 block">Indicators shared by multiple incidents</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-obsidian-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Primary Hub Location</span>
            <MapPin className="w-4 h-4 text-pink-400" />
          </div>
          <span className="text-2xl font-extrabold text-white mt-2 block">{stats.primary_hub_location || '—'}</span>
          <span className="text-[11px] text-slate-400 mt-1 block">{stats.primary_hub_count || 0} reported incidents</span>
        </div>

      </div>

      {/* Analytics Chart & Top Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Most Connected Indicators Bar Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-3xl border border-obsidian-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-100">Most Connected Properties (Degree Count)</h3>
              <p className="text-xs text-slate-400">Top shared indicators linking multiple cybercrime reports</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30">
              Graph Analytics
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Indicators List */}
        <div className="glass-panel p-6 rounded-3xl border border-obsidian-800 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100 mb-1">Key Indicator Hubs</h3>
            <p className="text-xs text-slate-400 mb-4">Indicators with highest incident degree</p>

            <div className="space-y-2.5">
              {stats.top_connected_properties.slice(0, 5).map((item: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-obsidian-900/80 border border-obsidian-800 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-cyber-cyan uppercase">{item.type}</span>
                    <p className="font-mono text-xs text-slate-200 font-semibold">{item.normalized_value}</p>
                  </div>
                  <span className="text-xs font-extrabold text-amber-400 bg-amber-400/10 px-2 py-1 rounded-lg border border-amber-400/20">
                    {item.connected_incidents_count} Incidents
                  </span>
                </div>
              ))}
            </div>
          </div>

          <Link
            href="/investigator/network"
            className="mt-4 w-full py-2.5 px-4 rounded-xl bg-obsidian-800 hover:bg-obsidian-700 text-slate-200 text-xs font-semibold text-center flex items-center justify-center gap-1.5 transition"
          >
            Inspect Most Connected Cluster <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

      </div>

      {/* Recent Incidents Table */}
      <div className="glass-panel p-6 rounded-3xl border border-obsidian-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-100">Recent Incident Submissions</h3>
          <span className="text-xs text-slate-400">Showing latest reports</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-obsidian-800 text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Incident ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-800/60">
              {stats.recent_incidents.map((inc: any) => (
                <tr key={inc.id} className="hover:bg-obsidian-900/40 transition">
                  <td className="py-3 px-4 font-mono font-bold text-cyber-cyan">{inc.id}</td>
                  <td className="py-3 px-4 font-medium text-slate-200">{inc.category}</td>
                  <td className="py-3 px-4 text-slate-300">{inc.location}</td>
                  <td className="py-3 px-4 text-slate-400">{new Date(inc.timestamp).toLocaleDateString('en-GB')}</td>
                  <td className="py-3 px-4">
                    <Link
                      href={`/investigator/incidents/${inc.id}`}
                      className="text-cyber-cyan font-semibold hover:underline flex items-center gap-1"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
