'use client';

import React from 'react';
import { CheckCircle2, Loader2, FileSearch, Database, Network, ShieldCheck } from 'lucide-react';

export type ProcessingStep = 'UPLOADING' | 'OCR' | 'EXTRACTING' | 'SAVING' | 'GRAPH' | 'COMPLETE';

interface StepperModalProps {
  currentStep: ProcessingStep;
  isOpen: boolean;
}

const STEPS: { key: ProcessingStep; label: string; icon: any }[] = [
  { key: 'UPLOADING', label: 'Uploading Evidence', icon: Loader2 },
  { key: 'OCR', label: 'PaddleOCR Text Extraction', icon: FileSearch },
  { key: 'EXTRACTING', label: 'Extracting & Normalizing Properties', icon: ShieldCheck },
  { key: 'SAVING', label: 'Saving to PostgreSQL', icon: Database },
  { key: 'GRAPH', label: 'Building Neo4j Knowledge Graph', icon: Network },
  { key: 'COMPLETE', label: 'Intelligence Analysis Complete', icon: CheckCircle2 },
];

export default function StepperModal({ currentStep, isOpen }: StepperModalProps) {
  if (!isOpen) return null;

  const currentIndex = STEPS.findIndex(s => s.key === currentStep);

  return (
    <div className="fixed inset-0 z-50 bg-obsidian-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="glass-panel max-w-md w-full p-6 rounded-2xl border border-obsidian-700 shadow-2xl space-y-6">
        
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-cyber-cyan/20 border border-cyber-cyan/30 text-cyber-cyan mx-auto flex items-center justify-center mb-3">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <h3 className="text-lg font-bold text-slate-100">CyberSaarthi Intelligence Pipeline</h3>
          <p className="text-xs text-slate-400 mt-1">Processing evidence image into knowledge graph indicators</p>
        </div>

        <div className="space-y-3">
          {STEPS.map((step, idx) => {
            const isFinished = idx < currentIndex || currentStep === 'COMPLETE';
            const isCurrent = idx === currentIndex && currentStep !== 'COMPLETE';
            const Icon = step.icon;

            return (
              <div
                key={step.key}
                className={`flex items-center gap-3 p-3 rounded-xl border transition ${
                  isFinished
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : isCurrent
                    ? 'bg-cyber-cyan/15 border-cyber-cyan/40 text-cyber-cyan font-semibold'
                    : 'bg-obsidian-900/40 border-obsidian-800 text-slate-500'
                }`}
              >
                {isFinished ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <Icon className="w-5 h-5 text-cyber-cyan animate-spin shrink-0" />
                ) : (
                  <div className="w-5 h-5 rounded-full border border-obsidian-700 shrink-0 flex items-center justify-center text-[10px]">
                    {idx + 1}
                  </div>
                )}

                <span className="text-xs">{step.label}</span>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
