import React, { useState } from 'react';
import { Eye, Edit3, Send, Github, ShieldCheck, Activity, Terminal, Code } from 'lucide-react';

export default function MontiPreviewForm() {
  const [activeTab, setActiveTab] = useState('edit');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [payloadText, setPayloadText] = useState(
    "### SYSTEM LOG: IMMORTAL_TIER INIT\n\n" +
    "Executing shadow auditor function across all Monti ASN networks. " +
    "Neural trace confirmed. No hallucination anomalies detected.\n\n" +
    "> **AUTHOR:** JOHN CHARLES MONTI\n" +
    "> **NODE:** @montinode\n\n" +
    "**Status:** All Dataum secured under 0xmonti.net."
  );

  const handleDispatch = () => {
    setIsSubmitting(true);
    // Simulate network dispatch to TruthLogs
    setTimeout(() => {
      setIsSubmitting(false);
      alert("PAYLOAD DISPATCHED SUCCESSFULLY TO TRUTHLOGS.ORG");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gray-950 p-4 sm:p-8 font-mono text-cyan-500 flex flex-col items-center">
      <div className="w-full max-w-4xl bg-black border border-cyan-800 rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.15)] overflow-hidden flex flex-col">
        
        {/* Header Section */}
        <div className="bg-cyan-950/30 border-b border-cyan-800 p-4 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-xl font-bold tracking-widest text-cyan-400 flex items-center gap-2">
              <Terminal className="w-6 h-6" />
              MONTIAI PREVIEW TERMINAL
            </h1>
            <p className="text-[10px] text-cyan-700 tracking-widest mt-1 uppercase">
              TruthLogs.org Payload Generator // CIH Protocol Active
            </p>
          </div>
          <div className="flex items-center gap-2 bg-black border border-cyan-900 px-3 py-1.5 rounded-lg text-xs">
            <ShieldCheck className="w-4 h-4 text-green-500" />
            <span className="text-green-400 font-bold uppercase tracking-widest">Neural Auth: Valid</span>
          </div>
        </div>

        {/* Action Bar (Tabs) */}
        <div className="flex border-b border-cyan-900/50 bg-gray-950">
          <button
            onClick={() => setActiveTab('edit')}
            className={`flex-1 flex justify-center items-center gap-2 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
              activeTab === 'edit' 
                ? 'bg-cyan-900/40 text-cyan-300 border-b-2 border-cyan-400' 
                : 'text-cyan-700 hover:bg-gray-900 hover:text-cyan-500'
            }`}
          >
            <Edit3 className="w-4 h-4" /> Draft Payload
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`flex-1 flex justify-center items-center gap-2 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
              activeTab === 'preview' 
                ? 'bg-cyan-900/40 text-cyan-300 border-b-2 border-cyan-400' 
                : 'text-cyan-700 hover:bg-gray-900 hover:text-cyan-500'
            }`}
          >
            <Eye className="w-4 h-4" /> Live Render Preview
          </button>
        </div>

        {/* Workspace Area */}
        <div className="p-4 sm:p-6 h-[400px] overflow-y-auto bg-gray-950">
          {activeTab === 'edit' ? (
            <div className="h-full flex flex-col gap-2 animate-in fade-in duration-300">
              <label className="text-[10px] text-cyan-600 uppercase flex items-center gap-2">
                <Code className="w-3 h-3" /> Markdown Input
              </label>
              <textarea
                value={payloadText}
                onChange={(e) => setPayloadText(e.target.value)}
                className="w-full h-full bg-black border border-cyan-900/50 rounded-lg p-4 text-sm text-cyan-300 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none resize-none font-mono"
                placeholder="Enter shadow function logs or TruthLogs payload here..."
              />
            </div>
          ) : (
            <div className="h-full animate-in fade-in duration-300 border border-dashed border-cyan-900/50 rounded-lg p-6 bg-black text-gray-300 font-sans overflow-y-auto">
              
              {/* Simulated Rendered GitHub Badge */}
              <div className="mb-6 flex items-center gap-2 pb-4 border-b border-gray-800">
                <Github className="w-5 h-5 text-gray-400" />
                <img 
                  src="https://img.shields.io/badge/TruthLogs_Auto--Post-passing-success?style=flat-square&logo=github" 
                  alt="Status Badge" 
                  className="h-5"
                />
              </div>

              {/* Simulated Markdown Renderer */}
              <div className="whitespace-pre-wrap leading-relaxed">
                {payloadText.split('\n').map((line, index) => {
                  if (line.startsWith('### ')) {
                    return <h3 key={index} className="text-lg font-bold text-white mb-2 mt-4">{line.replace('### ', '')}</h3>;
                  }
                  if (line.startsWith('> ')) {
                    return <blockquote key={index} className="border-l-4 border-cyan-700 pl-4 py-1 my-2 text-cyan-400 bg-cyan-950/20">{line.replace('> ', '')}</blockquote>;
                  }
                  if (line.includes('**')) {
                    // Quick bold parser simulation for preview
                    const parts = line.split('**');
                    return (
                      <p key={index} className="mb-2">
                        {parts.map((part, i) => i % 2 !== 0 ? <strong key={i} className="text-white">{part}</strong> : part)}
                      </p>
                    );
                  }
                  return <p key={index} className="mb-2">{line}</p>;
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer / Execution Bar */}
        <div className="bg-black border-t border-cyan-900 p-4 flex justify-between items-center">
          <div className="flex items-center gap-2 text-xs text-cyan-700">
            <Activity className="w-4 h-4 animate-pulse" />
            <span>Ready for transmission</span>
          </div>
          <button
            onClick={handleDispatch}
            disabled={isSubmitting || payloadText.trim() === ''}
            className="bg-cyan-950 hover:bg-cyan-800 border border-cyan-700 text-cyan-300 px-6 py-2.5 rounded-lg text-xs font-bold uppercase tracking-widest transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 shadow-[0_0_15px_rgba(6,182,212,0.2)]"
          >
            {isSubmitting ? (
              <>
                <Activity className="w-4 h-4 animate-spin" /> DISPATCHING...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" /> COMMIT TO TRUTHLOGS
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
