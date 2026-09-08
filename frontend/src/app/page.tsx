'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, ShieldCheck, FileText, MapPin, AlertCircle, Sparkles, ArrowRight } from 'lucide-react';
import StepperModal, { ProcessingStep } from '@/components/StepperModal';
import { cyberEngine } from '@/lib/cybersaarthi_engine';

export default function CitizenPortal() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('Kochi');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<ProcessingStep>('UPLOADING');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsProcessing(true);
    setCurrentStep('UPLOADING');

    // Simulate real-time backend pipeline stages
    await new Promise(r => setTimeout(r, 600));
    setCurrentStep('OCR');
    await new Promise(r => setTimeout(r, 700));
    setCurrentStep('EXTRACTING');
    await new Promise(r => setTimeout(r, 600));
    setCurrentStep('SAVING');
    await new Promise(r => setTimeout(r, 600));
    setCurrentStep('GRAPH');
    await new Promise(r => setTimeout(r, 700));

    // Process through engine
    const inc = await cyberEngine.processEvidenceUpload(file, description, location);
    setCurrentStep('COMPLETE');
    await new Promise(r => setTimeout(r, 500));

    router.push(`/result/${inc.id}`);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 w-full flex-1 flex flex-col justify-center">
      
      {/* Hero Title */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan text-xs font-semibold mb-4">
          <Sparkles className="w-3.5 h-3.5" /> SIH 2026 Cyber Intelligence Prototype
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
          Report Suspicious Cyber Activity
        </h1>
        <p className="text-slate-400 text-sm mt-2 max-w-xl mx-auto">
          Upload cybercrime screenshots or financial fraud evidence. Our OCR engine automatically extracts indicators to connect recurring crime networks.
        </p>
      </div>

      {/* Upload Form Card */}
      <div className="glass-panel p-8 rounded-3xl border border-obsidian-800 shadow-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* File Drag-and-drop zone */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Upload Evidence Screenshot (PNG, JPG, JPEG, PDF) *
            </label>
            <div className="relative border-2 border-dashed border-obsidian-700 hover:border-cyber-cyan/60 rounded-2xl p-8 text-center bg-obsidian-900/60 transition group cursor-pointer">
              <input
                type="file"
                accept="image/png, image/jpeg, image/jpg, application/pdf"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                required
              />
              
              <div className="w-14 h-14 rounded-2xl bg-cyber-cyan/15 text-cyber-cyan mx-auto flex items-center justify-center mb-3 group-hover:scale-110 transition">
                <Upload className="w-7 h-7" />
              </div>

              {file ? (
                <div>
                  <p className="text-sm font-bold text-cyber-cyan break-all">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB • Ready for OCR extraction</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Click to browse or drop cybercrime evidence here
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Supports bank transaction receipts, WhatsApp scam chats, phishing URLs
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Description & Location Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-cyber-cyan" /> Incident Description
              </label>
              <textarea
                rows={3}
                placeholder="Describe how the fraud occurred..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-obsidian-900 border border-obsidian-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:border-cyber-cyan focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-pink-400" /> Incident Location
              </label>
              <input
                type="text"
                placeholder="e.g. Kochi, Kerala"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-obsidian-900 border border-obsidian-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:border-cyber-cyan focus:outline-none mb-3"
              />

              <div className="p-3 rounded-xl bg-obsidian-900/60 border border-obsidian-800 text-[11px] text-slate-400 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-cyber-cyan shrink-0 mt-0.5" />
                <span>Submissions are stored securely for intelligence graph discovery. No automated FIR is registered.</span>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || isProcessing}
            className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-cyber-cyan via-cyber-blue to-cyber-purple text-obsidian-950 font-extrabold text-sm tracking-wide flex items-center justify-center gap-2 hover:opacity-95 transition shadow-lg shadow-cyber-cyan/20 disabled:opacity-50"
          >
            Submit Evidence & Run Graph Extraction <ArrowRight className="w-4 h-4" />
          </button>

        </form>

        <p className="text-center text-xs text-slate-500 mt-6">
          "Your submission can help identify recurring cybercrime patterns."
        </p>
      </div>

      <StepperModal isOpen={isProcessing} currentStep={currentStep} />
    </div>
  );
}
