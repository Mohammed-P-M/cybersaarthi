'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Shield, Network, FileText, Search, Activity, UserCheck } from 'lucide-react';

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/investigator/network?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-obsidian-950/90 backdrop-blur-md border-b border-obsidian-800 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-cyan to-cyber-blue p-0.5 shadow-lg shadow-cyber-cyan/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-obsidian-950 rounded-[10px] flex items-center justify-center">
              <Shield className="w-5 h-5 text-cyber-cyan" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyber-cyan bg-clip-text text-transparent">
                CyberSaarthi
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-cyber-blue/20 text-cyber-cyan border border-cyber-cyan/30">
                SIH 2026
              </span>
            </div>
            <p className="text-xs text-slate-400">Knowledge Graph Intelligence Platform</p>
          </div>
        </Link>

        {/* Investigator Quick Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md mx-6">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Global Search (UPI, Phone, Transaction ID, URL, Email)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-obsidian-900 border border-obsidian-700 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan transition-all"
            />
          </div>
        </form>

        {/* Navigation links */}
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === '/' 
                ? 'bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-900'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            Citizen Portal
          </Link>

          <Link
            href="/investigator"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === '/investigator' 
                ? 'bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-900'
            }`}
          >
            <Activity className="w-4 h-4" />
            Dashboard
          </Link>

          <Link
            href="/investigator/network"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname.startsWith('/investigator/network') 
                ? 'bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-900'
            }`}
          >
            <Network className="w-4 h-4 text-cyber-cyan" />
            Graph Canvas
          </Link>
        </nav>

      </div>
    </header>
  );
}
