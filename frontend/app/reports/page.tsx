'use client';

import React from 'react';
import Layout from '@/components/Layout';
import { FileText, Download, BarChart2, Calendar, FileSpreadsheet, Send } from 'lucide-react';

export default function ReportsPage() {
  return (
    <Layout>
      <div className="space-y-8 max-w-7xl mx-auto">
        <div className="flex justify-between items-end border-b border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-cyan-500/20">
              <FileText className="text-white w-7 h-7" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-white">Reporting Center</h1>
              <p className="text-slate-400 mt-1">Generate, schedule, and distribute automated performance dossiers.</p>
            </div>
          </div>
          <button className="bg-gradient-to-r from-cyan-600 to-cyan-600 hover:from-cyan-500 hover:to-cyan-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-cyan-500/25 flex items-center gap-2">
            <BarChart2 size={18} /> Generate Custom Report
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ReportCard 
            title="Weekly SEO Digest"
            description="Aggregated view of portfolio SEO metrics and critical crawler flags."
            icon={<FileText className="text-slate-400 w-6 h-6" />}
            tag="Automated"
          />
          <ReportCard 
            title="Outreach Performance"
            description="End-to-end CRM campaign metrics, reply rates, and AI agent output logs."
            icon={<BarChart2 className="text-slate-400 w-6 h-6" />}
            tag="Manual"
          />
          <ReportCard 
            title="Financial Overview"
            description="Burn rate diagnostics and P&L summaries exported to XLS."
            icon={<FileSpreadsheet className="text-slate-400 w-6 h-6" />}
            tag="Scheduled"
          />
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl mt-8">
           <h3 className="text-xl font-bold text-white mb-6">Scheduled Reports</h3>
           <div className="h-48 border-2 border-dashed border-slate-700/50 rounded-xl flex flex-col items-center justify-center text-center">
             <Calendar className="text-slate-500 w-12 h-12 mb-3" />
             <p className="text-slate-300 font-semibold mb-1">No Active Schedules</p>
             <p className="text-slate-500 text-sm max-w-sm">Setup recurring automated emails to dispatch directly to stakeholders via the Reporting Center.</p>
           </div>
        </div>
      </div>
    </Layout>
  );
}

function ReportCard({ title, description, icon, tag }: { title: string, description: string, icon: React.ReactNode, tag: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-cyan-500/50 transition-all group">
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-slate-950 rounded-lg group-hover:bg-slate-800 transition-colors">
          {icon}
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-800 px-2 py-1 rounded">
          {tag}
        </span>
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-sm mb-6 leading-relaxed bg-transparent min-h-[40px]">{description}</p>
      
      <div className="flex items-center gap-2">
        <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
          <Download size={16} /> Download
        </button>
        <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
          <Send size={16} /> Distribute
        </button>
      </div>
    </div>
  );
}
