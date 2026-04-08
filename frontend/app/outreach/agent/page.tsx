'use client';

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import OutreachTabs from '@/components/OutreachTabs';
import { Target, User, Building, Mail, Sparkles, Send, Copy, AlertCircle } from 'lucide-react';

export default function OutreachAgentPage() {
  const [loading, setLoading] = useState(false);
  const [industry, setIndustry] = useState('');
  const [persona, setPersona] = useState('');
  const [context, setContext] = useState('');
  const [leads, setLeads] = useState<any[]>([]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/outreach/agent/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ industry, target_persona: persona, company_context: context }),
      });

      if (!response.ok) throw new Error('API Error');
      const data = await response.json();
      setLeads(data.leads || []);
    } catch (err) {
      alert('Failed to generate leads via AI agent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Outreach Hub</h1>
        <OutreachTabs currentTab="agent" />
        
        <div className="flex items-center gap-4 pb-6 mt-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-fuchsia-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-fuchsia-500/20">
            <Sparkles className="text-white w-7 h-7" />
          </div>
          <div>
            <h2 className="text-2xl font-extrabold text-white">AI Lead Prospector</h2>
            <p className="text-slate-400 mt-1">Autonomous agent that predicts, researches, and writes perfect cold outreach pipelines.</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-12 gap-8">
          {/* Agent Parameters Form */}
          <div className="lg:col-span-4">
            <form onSubmit={handleGenerate} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl sticky top-6">
              <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <Target className="w-5 h-5 text-cyan-400" />
                Targeting Parameters
              </h3>
              
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">My Value Proposition</label>
                  <textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    required
                    rows={3}
                    placeholder="E.g., We sell a B2B SaaS platform that cuts AWS costs by 20% using dynamic load balancing."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Target Industry</label>
                  <input
                    type="text"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    required
                    placeholder="E.g., FinTech, E-Commerce, Digital Health"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Buyer Persona / Title</label>
                  <input
                    type="text"
                    value={persona}
                    onChange={(e) => setPersona(e.target.value)}
                    required
                    placeholder="E.g., CTO, VP of Engineering, Founders"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-4 bg-gradient-to-r from-cyan-600 to-fuchsia-600 hover:from-cyan-500 hover:to-fuchsia-500 text-white font-bold px-6 py-4 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 disabled:opacity-50"
                >
                  {loading ? (
                    <span className="animate-pulse flex items-center gap-2">
                      <Sparkles size={18} /> Mining Data...
                    </span>
                  ) : (
                    <>
                      <Send size={18} /> Deploy Agent
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Lead Pipeline Results */}
          <div className="lg:col-span-8">
            {!loading && leads.length === 0 && (
              <div className="h-full min-h-[400px] border-2 border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8 text-center bg-slate-900/30">
                <Target className="w-16 h-16 text-slate-700 mb-4" />
                <h3 className="text-xl font-bold text-slate-300 mb-2">Agent Idle</h3>
                <p className="max-w-md">Configure your targeting parameters on the left and deploy the SDR agent to begin generating hyperspecific lead pipelines.</p>
              </div>
            )}

            {loading && (
              <div className="grid grid-cols-1 gap-6">
                 {[1, 2, 3].map(i => (
                   <div key={i} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
                     <div className="h-4 bg-slate-800 rounded w-1/4 mb-4" />
                     <div className="h-3 bg-slate-800 rounded w-1/2 mb-6" />
                     <div className="h-20 bg-slate-800 rounded" />
                   </div>
                 ))}
              </div>
            )}

            {!loading && leads.length > 0 && (
              <div className="grid grid-cols-1 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {leads.map((lead, idx) => (
                  <div key={idx} className="bg-slate-900 border border-slate-700 rounded-2xl p-1 overflow-hidden shadow-xl">
                    <div className="bg-slate-950 rounded-xl p-6 relative group">
                      
                      {/* High Intent Badge */}
                      <div className="absolute top-6 right-6 flex items-center gap-1.5 bg-green-500/10 text-green-400 px-3 py-1 rounded-full border border-green-500/20 text-xs font-bold uppercase tracking-wide">
                        <Sparkles size={12} /> High Intent Match
                      </div>

                      <div className="flex items-start gap-4 mb-6">
                        <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0 text-cyan-400">
                          <User size={24} />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-white mb-1">{lead.name}</h3>
                          <div className="flex items-center gap-4 text-sm text-slate-400">
                            <span className="flex items-center gap-1.5"><Building size={14} className="text-slate-500"/> {lead.title} at {lead.company}</span>
                            <span className="flex items-center gap-1.5"><Mail size={14} className="text-slate-500"/> {lead.email_guess}</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-4">
                        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">
                          <AlertCircle size={14} /> Agent Rationale
                        </div>
                        <p className="text-slate-300 text-sm leading-relaxed">{lead.rationale}</p>
                      </div>

                      <div className="bg-cyan-950/30 border border-cyan-500/20 rounded-lg p-5 relative group/draft">
                        <div className="flex items-center justify-between mb-3">
                          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest">
                            AI Output: Cold Intro Draft
                          </div>
                          <button 
                            onClick={() => navigator.clipboard.writeText(lead.custom_intro_line)}
                            className="bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-300 p-1.5 rounded transition"
                          >
                            <Copy size={14} />
                          </button>
                        </div>
                        <p className="text-white font-serif text-lg leading-relaxed italic border-l-2 border-cyan-500 pl-4">{lead.custom_intro_line}</p>
                      </div>

                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
