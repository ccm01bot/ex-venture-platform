'use client';

import React from 'react';
import Layout from '@/components/Layout';
import { FileText, Download, BarChart2, Calendar, FileSpreadsheet, Send } from 'lucide-react';
import { useState } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Data simulation maps representing core database matrices for the various dashboards
const DATA_SCHEMAS = {
  seo: [
    { Date: '2026-04-10', Endpoint: 'https://ex-venture.com/home', Speed_Index: '1.2s', TTFB: '0.3s', CLS_Score: 0.01, Status: 'PASS' },
    { Date: '2026-04-11', Endpoint: 'https://ex-venture.com/portfolio', Speed_Index: '2.4s', TTFB: '0.8s', CLS_Score: 0.12, Status: 'WARNING' },
    { Date: '2026-04-12', Endpoint: 'https://ex-venture.com/contact', Speed_Index: '1.4s', TTFB: '0.4s', CLS_Score: 0.04, Status: 'PASS' }
  ],
  outreach: [
    { Campaign: 'Global SaaS Syndicate', Sent: 450, Opens: 320, Replies: 85, Clicks: 112, Bounced: 3 },
    { Campaign: 'Enterprise Q2 Expansion', Sent: 1200, Opens: 740, Replies: 130, Clicks: 250, Bounced: 15 },
    { Campaign: 'Seed Stage Accelerator', Sent: 300, Opens: 290, Replies: 145, Clicks: 180, Bounced: 0 }
  ],
  financial: [
    { Month: 'Q4-2025', Burn_Rate: '$420,000', MRR: '$850,000', Net_Income: '$210,000', Runway_Months: 24 },
    { Month: 'Q1-2026', Burn_Rate: '$380,000', MRR: '$950,000', Net_Income: '$340,000', Runway_Months: 32 },
    { Month: 'Q2-2026', Burn_Rate: '$410,000', MRR: '$1,150,000', Net_Income: '$450,000', Runway_Months: 48 }
  ]
};

export default function ReportsPage() {
  const handleGenericDownload = () => {
    const doc = new jsPDF();
    doc.setFontSize(22);
    doc.text("Global System Diagnostic", 14, 22);
    
    doc.setFontSize(11);
    doc.setTextColor(100);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
    
    const tableData = [
      ["Core Server", "Online", "100%"],
      ["AI Node", "Online", "100%"],
      ["Database Rows", "Synced", "84302"]
    ];
    
    autoTable(doc, {
      startY: 40,
      head: [["Module", "Status", "Value"]],
      body: tableData,
      theme: 'grid',
      headStyles: { fillColor: [6, 182, 212] }
    });
    
    doc.save("Global_System_Diagnostic.pdf");
  };

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
          <button 
            onClick={handleGenericDownload}
            className="bg-gradient-to-r from-cyan-600 to-cyan-600 hover:from-cyan-500 hover:to-cyan-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-cyan-500/25 flex items-center gap-2"
          >
            <BarChart2 size={18} /> Generate Custom Report
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ReportCard 
            title="Weekly SEO Digest"
            type="seo"
            description="Aggregated view of portfolio SEO metrics and critical crawler flags."
            icon={<FileText className="text-slate-400 w-6 h-6" />}
            tag="Automated"
          />
          <ReportCard 
            title="Outreach Performance"
            type="outreach"
            description="End-to-end CRM campaign metrics, reply rates, and AI agent output logs."
            icon={<BarChart2 className="text-slate-400 w-6 h-6" />}
            tag="Manual"
          />
          <ReportCard 
            title="Financial Overview"
            type="financial"
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

// Utilized heavy autoTable rendering to enforce clean, visual matrix conversions dynamically mapped into the user's explicit PDF requirement.
function generateAndDownloadPDF(title: string, data: any[]) {
  if (!data || data.length === 0) return;
  const keys = Object.keys(data[0]);
  const rows = data.map(row => keys.map(k => row[k]));

  const doc = new jsPDF();
  doc.setFontSize(18);
  doc.text(title, 14, 22);
  
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);

  autoTable(doc, {
    startY: 38,
    head: [keys],
    body: rows,
    theme: 'striped',
    headStyles: { fillColor: [15, 23, 42] }, // Slate-900 header mapping
    styles: { fontSize: 9 }
  });

  doc.save(`${title.replace(/ /g, '_')}_Report.pdf`);
}

function ReportCard({ title, type, description, icon, tag }: { title: string, type: string, description: string, icon: React.ReactNode, tag: string }) {
  const [downloading, setDownloading] = useState(false);
  const [weeksAgo, setWeeksAgo] = useState(0);

  const handleDownload = async () => {
    setDownloading(true);
    
    if (type === 'seo') {
      try {
        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scans/report/weekly?weeks_ago=${weeksAgo}`);
        if (!resp.ok) {
           window.alert("Failed to fetch historical database metrics.");
           setDownloading(false);
           return;
        }
        
        const json = await resp.json();
        
        generateAndDownloadPDF(`${title} (Week of ${json.week_start})`, json.scans);
      } catch (err) {
        window.alert("Network failure querying backend for SEO digest.");
      }
    } else {
      setTimeout(() => {
        const dbMatrix = DATA_SCHEMAS[type as keyof typeof DATA_SCHEMAS];
        generateAndDownloadPDF(title, dbMatrix);
      }, 1200);
    }
    
    setDownloading(false);
  };

  const handleDistribute = () => {
    window.alert(`SUCCESS: Simulated ${title} distribution.\n\nIn a full production environment, this triggers the Resend API to blast the CSV directly to all Active Stakeholder inboxes.`);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-cyan-500/50 transition-all group flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-slate-950 rounded-lg group-hover:bg-slate-800 transition-colors">
          {icon}
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-800 px-2 py-1 rounded">
          {tag}
        </span>
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-sm mb-6 flex-grow leading-relaxed bg-transparent">{description}</p>
      
      {type === 'seo' && (
        <div className="mb-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1 block">Historical Bracket</label>
          <select 
            className="w-full bg-slate-950 text-slate-300 border border-slate-800 rounded-lg p-2 text-sm focus:border-cyan-500 outline-none"
            value={weeksAgo}
            onChange={(e) => setWeeksAgo(Number(e.target.value))}
          >
             <option value={0}>Current Week</option>
             <option value={1}>1 Week Ago</option>
             <option value={2}>2 Weeks Ago</option>
             <option value={3}>3 Weeks Ago</option>
             <option value={4}>4 Weeks Ago</option>
          </select>
        </div>
      )}

      <div className="flex items-center gap-2 mt-auto">
        <button 
          onClick={handleDownload}
          disabled={downloading}
          className={`flex-1 text-white text-sm font-semibold py-2.5 rounded-lg transition-all flex items-center justify-center gap-2 ${
            downloading ? 'bg-cyan-600/50 animate-pulse' : 'bg-slate-800 hover:bg-slate-700'
          }`}
        >
          {downloading ? (
            <>Aggregating...</>
          ) : (
            <><Download size={16} /> Download</>
          )}
        </button>
        <button 
          onClick={handleDistribute}
          className="flex-1 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Send size={16} /> Distribute
        </button>
      </div>
    </div>
  );
}
