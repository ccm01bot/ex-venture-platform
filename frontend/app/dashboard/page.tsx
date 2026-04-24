'use client';

import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { BarChart3, ArrowRight, Activity, Globe, Search, Settings, Trash2 } from 'lucide-react';

interface Company {
  id: string;
  name: string;
  url: string;
  industry_tags: string[];
  overall_score?: number;
}

export default function DashboardPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies`
      );

      if (response.ok) {
        const data = await response.json();
        setCompanies(data);
      }
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this company? This cannot be undone.')) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies/${id}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        await fetchCompanies();
      }
    } catch (error) {
      console.error('Failed to delete company:', error);
    }
  };

  const calculateMacroStats = () => {
    if (companies.length === 0) return { avgScore: 0, criticalCount: 0 };
    let totalScore = 0;
    let scoredCount = 0;
    let criticals = 0;

    companies.forEach(c => {
      if (c.overall_score) {
        totalScore += c.overall_score;
        scoredCount++;
      }
      if (c.overall_score && c.overall_score < 70) {
        criticals++;
      }
    });

    return {
      avgScore: scoredCount > 0 ? Math.round(totalScore / scoredCount) : 0,
      criticalCount: criticals
    };
  };

  const stats = calculateMacroStats();

  return (
    <Layout>
      <div className="space-y-8 animate-in fade-in duration-500">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 tracking-tight">Portfolio Dashboard</h1>
            <p className="text-slate-400 mt-2">Manage and optimize your active ventures.</p>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* Macro Stats Banner */}
            {companies.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden backdrop-blur-md">
                <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 blur-[80px] rounded-full pointer-events-none"></div>
                <div className="relative z-10 flex items-center gap-6 p-4 border border-slate-800/80 rounded-xl bg-slate-950/40">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 ${stats.avgScore > 80 ? 'border-emerald-500' : stats.avgScore > 60 ? 'border-amber-500' : 'border-slate-700'} shadow-lg bg-slate-900`}>
                    <span className="text-2xl font-black text-white">{stats.avgScore || '-'}</span>
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Avg Portfolio SEO</p>
                    <p className="text-2xl font-bold text-white mt-1">Global SEO Baseline</p>
                  </div>
                </div>
                <div className="relative z-10 flex items-center justify-between p-6 border border-slate-800/80 rounded-xl bg-slate-950/40">
                  <div>
                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Attention Required</p>
                    <p className="text-2xl font-bold text-white"><span className="text-red-400">{stats.criticalCount}</span> Critical Entities</p>
                  </div>
                  <Activity className={`w-12 h-12 ${stats.criticalCount > 0 ? 'text-red-500' : 'text-emerald-500'} opacity-80`} />
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {companies.map((company) => (
                <CompanyCard key={company.id} company={company} onDelete={() => handleDelete(company.id)} />
              ))}
            </div>
          </>
        )}

        {companies.length === 0 && !loading && (
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-12 text-center shadow-2xl relative overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-500/20 blur-[100px] rounded-full pointer-events-none"></div>
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-16 h-16 bg-slate-800/80 rounded-2xl flex items-center justify-center mb-4 border border-slate-700/50 shadow-inner">
                <Globe className="w-8 h-8 text-cyan-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">No Companies Yet</h2>
              <p className="text-slate-400 mb-6 max-w-sm mx-auto">Start building your pipeline by adding your first portfolio company to track.</p>
              <a
                href="/companies"
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold px-8 py-3 rounded-full shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all hover:scale-105 hover:-translate-y-1 inline-flex items-center gap-2"
              >
                Add First Company <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function CompanyCard({ company, onDelete }: { company: Company, onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleExpand = async () => {
    if (!expanded && !data) {
      setLoading(true);
      try {
        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/company/${company.id}/latest`);
        if (resp.ok) {
          const result = await resp.json();
          setData(result);
        }
      } catch (err) {
        console.error("No cached scan");
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  return (
    <div 
      className="group bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-2xl overflow-hidden hover:border-cyan-500/50 hover:bg-slate-800/60 transition-all duration-500 shadow-[0_10px_40px_-10px_rgba(6,182,212,0.1)] relative"
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-500/10 to-fuchsia-500/10 blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>

      <div 
        className="p-6 cursor-pointer relative z-10"
        onClick={handleExpand}
      >
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-xl font-bold text-white mb-1 group-hover:text-cyan-400 transition-colors">{company.name}</h3>
            <a
              href={company.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
              onClick={(e) => e.stopPropagation()}
            >
              <Globe className="w-3.5 h-3.5" /> {company.url}
            </a>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="text-slate-500 hover:text-red-400 bg-slate-800/50 hover:bg-red-400/10 p-2 rounded-full transition-all"
            title="Delete Company"
          >
            <Trash2 size={16} />
          </button>
        </div>

        {company.industry_tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {company.industry_tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] uppercase tracking-wider font-bold bg-slate-800/80 text-fuchsia-400/90 border border-fuchsia-500/20 px-2.5 py-1 rounded shadow-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="space-y-4 pt-4 border-t border-slate-800/60">
          <div className="flex items-center justify-between bg-slate-950/50 p-3 rounded-lg border border-slate-800/50">
            <span className="text-slate-400 text-sm font-medium flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" /> Health Score
            </span>
            <div className="flex items-center gap-2 bg-slate-800 px-3 py-1 rounded shadow-inner">
              <span className="font-black text-cyan-400">{company.overall_score || '-'}</span>
            </div>
          </div>

          <div className="flex gap-3">
            <Link href="/scan" onClick={(e) => e.stopPropagation()} className="flex-1 bg-cyan-600/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 transition-all text-sm font-bold py-2.5 rounded-lg flex items-center justify-center gap-2">
              <Search className="w-4 h-4" /> Scan Logic
            </Link>
            <Link href="/companies" onClick={(e) => e.stopPropagation()} className="flex-1 bg-slate-800 hover:bg-slate-700 text-white transition-all border border-slate-700 text-sm font-bold py-2.5 rounded-lg flex items-center justify-center gap-2">
              <Settings className="w-4 h-4" /> Manage
            </Link>
          </div>
        </div>
      </div>

      {/* EXPANDABLE SEO DATA SECTION */}
      {expanded && (
        <div className="bg-slate-950/80 border-t border-slate-800/60 p-6 relative z-10 animate-in slide-in-from-top-2">
          {loading ? (
             <div className="flex justify-center items-center py-6">
                <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
             </div>
          ) : data ? (
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3">SEO Diagnostics</h4>
              
              <div className="grid grid-cols-2 gap-3">
                 <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Load Time</p>
                    <p className={`text-lg font-black ${data.load_time_ms < 1500 ? 'text-emerald-400' : 'text-amber-400'}`}>{data.load_time_ms}ms</p>
                 </div>
                 <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Total Words</p>
                    <p className="text-lg font-black text-white">{data.word_count.toLocaleString()}</p>
                 </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
                 <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-3">Issues Found</p>
                 <div className="space-y-2 max-h-[150px] overflow-y-auto pr-1">
                   {data.issues.length === 0 ? (
                      <p className="text-xs text-emerald-400">No issues found!</p>
                   ) : (
                      data.issues.map((i: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                          <span className={i.severity === 'critical' ? 'text-red-400' : i.severity === 'warning' ? 'text-amber-400' : 'text-blue-400'}>•</span>
                          {i.message}
                        </div>
                      ))
                   )}
                 </div>
              </div>

              <div className="flex justify-between items-center text-xs text-slate-400 mt-2 pt-2 border-t border-slate-800/60">
                 <span>{data.passes.length} checks passed</span>
                 <span className="flex items-center gap-1">HTTPS: {data.has_ssl ? '✅' : '❌'}</span>
                 <span className="flex items-center gap-1">Mobile: {data.has_viewport ? '✅' : '❌'}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-6">
               <p className="text-sm text-slate-400 mb-3">No scan data found for this company.</p>
               <Link href="/scan" className="text-xs font-bold text-cyan-400 hover:text-cyan-300 underline underline-offset-4">Run an initial scan →</Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
