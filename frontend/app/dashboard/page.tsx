'use client';

import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { BarChart3, ArrowRight, Activity, Globe } from 'lucide-react';

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
        `${process.env.NEXT_PUBLIC_API_URL}/api/companies`
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
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {companies.map((company) => (
              <CompanyCard key={company.id} company={company} />
            ))}
          </div>
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
                Add First Company <ArrowRight className="w-4 h-4"/>
              </a>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function CompanyCard({ company }: { company: Company }) {
  return (
    <div className="group bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-2xl p-6 hover:border-cyan-500/50 hover:bg-slate-800/60 transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_10px_40px_-10px_rgba(6,182,212,0.15)] relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-500/10 to-fuchsia-500/10 blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
      
      <div className="flex justify-between items-start mb-6 relative z-10">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">{company.name}</h3>
          <a
            href={company.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
          >
            {company.url}
          </a>
        </div>
      </div>

      {company.industry_tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6 relative z-10">
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

      <div className="space-y-4 pt-4 border-t border-slate-800/60 relative z-10">
        <div className="flex items-center justify-between bg-slate-950/50 p-3 rounded-lg border border-slate-800/50">
          <span className="text-slate-400 text-sm font-medium flex items-center gap-2"><Activity className="w-4 h-4 text-emerald-400"/> Health Score</span>
          <div className="flex items-center gap-2 bg-slate-800 px-3 py-1 rounded shadow-inner">
            <span className="font-black text-cyan-400">{company.overall_score || '-'}</span>
          </div>
        </div>

        <div className="flex gap-3">
          <button className="flex-1 bg-cyan-600/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 transition-all text-sm font-bold py-2.5 rounded-lg flex items-center justify-center gap-2">
            Scan Logic
          </button>
          <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white transition-all border border-slate-700 text-sm font-bold py-2.5 rounded-lg">
            Manage
          </button>
        </div>
      </div>
    </div>
  );
}
