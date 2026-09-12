'use client';

import React, { useEffect, useState } from 'react';
import { Filter, RotateCcw, MapPin, Layers, Shield, Hash } from 'lucide-react';
import { getGraphFacets } from '@/lib/api';
import { CRIME_CATEGORIES } from '@/lib/crimeCategories';

export interface FilterOptions {
  propertyTypes: string[];
  location: string;
  category: string;
  minConnections: number;
}

interface FilterSidebarProps {
  filters: FilterOptions;
  onChangeFilters: (newFilters: FilterOptions) => void;
  onReset: () => void;
}

const ALL_PROP_TYPES = [
  { id: 'PHONE', label: 'Phone Number' },
  { id: 'UPI', label: 'UPI Handle' },
  { id: 'TRANSACTION_ID', label: 'Transaction ID' },
  { id: 'URL', label: 'Phishing URL' },
  { id: 'EMAIL', label: 'Email Address' },
  { id: 'LOCATION', label: 'Location' },
  { id: 'CRIME_CATEGORY', label: 'Crime Category' },
];

export default function FilterSidebar({ filters, onChangeFilters, onReset }: FilterSidebarProps) {
  const [locations, setLocations] = useState<string[]>([]);
  const [categories, setCategories] = useState<{ id: string; label: string }[]>([...CRIME_CATEGORIES]);

  useEffect(() => {
    let active = true;
    getGraphFacets().then((data) => {
      if (!active) return;
      setLocations(data.locations || []);
      if (Array.isArray(data.categories) && data.categories.length) setCategories(data.categories);
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  const togglePropType = (typeId: string) => {
    const exists = filters.propertyTypes.includes(typeId);
    const updated = exists ? filters.propertyTypes.filter(t => t !== typeId) : [...filters.propertyTypes, typeId];
    onChangeFilters({ ...filters, propertyTypes: updated });
  };

  return (
    <div className="w-72 glass-panel border-r border-obsidian-800 h-full p-5 flex flex-col justify-between">
      <div className="space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-obsidian-800">
          <div className="flex items-center gap-2 text-cyber-cyan font-bold text-sm"><Filter className="w-4 h-4" /> Graph Filters</div>
          <button onClick={onReset} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition"><RotateCcw className="w-3 h-3" /> Reset</button>
        </div>

        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2.5 flex items-center gap-1.5"><Layers className="w-3.5 h-3.5 text-cyber-cyan" /> Property Types</span>
          <div className="space-y-1.5">
            {ALL_PROP_TYPES.map(pt => {
              const active = filters.propertyTypes.includes(pt.id);
              return <button key={pt.id} onClick={() => togglePropType(pt.id)} className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium border transition ${active ? 'bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/40' : 'bg-obsidian-900/60 text-slate-400 border-obsidian-800 hover:text-slate-200'}`}><span>{pt.label}</span><span className={`w-2 h-2 rounded-full ${active ? 'bg-cyber-cyan' : 'bg-obsidian-700'}`} /></button>;
            })}
          </div>
        </div>

        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-pink-400" /> Location Filter</span>
          <select value={filters.location} onChange={(e) => onChangeFilters({ ...filters, location: e.target.value })} className="w-full bg-obsidian-900 border border-obsidian-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:border-cyber-cyan focus:outline-none">
            <option value="">All Locations</option>
            {locations.map(location => <option key={location} value={location}>{location}</option>)}
          </select>
          <p className="text-[10px] text-slate-500 mt-1">List updates automatically from reported cases.</p>
        </div>

        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-amber-400" /> Crime Category</span>
          <select value={filters.category} onChange={(e) => onChangeFilters({ ...filters, category: e.target.value })} className="w-full bg-obsidian-900 border border-obsidian-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:border-cyber-cyan focus:outline-none">
            <option value="">All Categories</option>
            {categories.map(category => <option key={category.id} value={category.id}>{category.label}</option>)}
          </select>
        </div>

        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5"><Hash className="w-3.5 h-3.5 text-emerald-400" /> Min Connections: <span className="text-slate-100 font-bold ml-1">{filters.minConnections}</span></span>
          <input type="range" min="1" max="10" value={filters.minConnections} onChange={(e) => onChangeFilters({ ...filters, minConnections: parseInt(e.target.value) })} className="w-full accent-cyber-cyan bg-obsidian-800 rounded-lg" />
        </div>
      </div>
      <div className="text-[11px] text-slate-500 text-center border-t border-obsidian-800 pt-3">CyberSaarthi Graph Analytics Engine v1.1</div>
    </div>
  );
}
