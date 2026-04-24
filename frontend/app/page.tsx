'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '@/components/Layout';
import { Layers, Activity, Zap } from 'lucide-react';

export default function Home() {
  const [stats, setStats] = useState({
    total_companies: 0,
    average_seo_score: 0,
    critical_issues: 0,
    scans_today: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scans/dashboard-stats`);
        if (resp.ok) {
          const data = await resp.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Failed to load dashboard stats", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500 pt-8">
        <div className="relative">
          <div className="absolute -top-12 -left-12 w-64 h-64 bg-cyan-500/20 rounded-full blur-[80px] pointer-events-none"></div>
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white via-slate-200 to-slate-500 mb-4 tracking-tight drop-shadow-sm">System Overview</h1>
          <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">Command Center. Monitor absolute portfolio health, execute SEO scanning cascades, and distribute brand equity globally.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 relative z-10">
          <StatCard label="Active Portfolio" value={stats.total_companies.toString()} type="normal" />
          <StatCard label="Avg Portfolio SEO" value={`${stats.average_seo_score}/100`} type="health" />
          <StatCard label="Critical Flags" value={stats.critical_issues.toString()} type="danger" />
          <StatCard label="Scans Today" value={stats.scans_today.toString()} type="normal" />
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
          <ActionCard
            title="Run Scanning Cascade"
            description="Trigger an asynchronous SEO mapping on all active companies to parse ranking gaps."
            href="/scan"
            icon={<Zap className="w-6 h-6 text-fuchsia-400" />}
          />
          <ActionCard
            title="Inject New Entity"
            description="Add a new company to the pipeline to begin tracking asset generation flows."
            href="/companies"
            icon={<Layers className="w-6 h-6 text-cyan-400" />}
          />
          <ActionCard
            title="Download Intelligence"
            description="Export all tracking state into a customized PDF or raw CSV data payload."
            href="/export"
            icon={<Activity className="w-6 h-6 text-emerald-400" />}
          />
        </div>
      </div>
    </Layout>
  );
}

function StatCard({ label, value, type }: { label: string; value: string; type: 'normal'|'danger'|'health' }) {
  let color = "text-white";
  if (type === 'danger') color = "text-red-400";
  if (type === 'health') color = "text-emerald-400";
  
  return (
    <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-2xl p-6 shadow-lg shadow-slate-900/20 hover:border-slate-700/80 transition-colors">
      <p className="text-slate-500 font-semibold text-xs tracking-wider uppercase mb-2">{label}</p>
      <p className={`text-4xl font-black ${color}`}>{value}</p>
    </div>
  );
}

function ActionCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="group block bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-2xl p-8 hover:border-cyan-500/50 hover:bg-slate-800/60 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_10px_30px_-10px_rgba(6,182,212,0.15)] relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-100 transition-opacity duration-500 group-hover:scale-110 group-hover:-translate-y-2 group-hover:translate-x-2">
        {icon}
      </div>
      <div className="w-12 h-12 bg-slate-800/80 rounded-xl flex items-center justify-center mb-6 shadow-inner border border-slate-700/50">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-100 mb-3">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
    </Link>
  );
}
