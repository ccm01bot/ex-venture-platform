'use client';

import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Trash2, Edit2, Settings, X, Globe, Key, ChevronDown, ChevronUp, AlertCircle, CheckCircle, Activity, Wand2, FileText, Search, Clock, Image, Link2, ShieldAlert, ShieldCheck, CheckCircle2, Shield, Lock, Smartphone, FileCode, MapPin, Share2, Code, XCircle, AlertTriangle, Info } from 'lucide-react';

const SEV_ICON = { critical: <XCircle className="w-4 h-4 text-red-400 shrink-0" />, warning: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />, info: <Info className="w-4 h-4 text-blue-400 shrink-0" /> };
const SEV_BG = { critical: 'bg-red-500/5 border-red-500/20', warning: 'bg-amber-500/5 border-amber-500/20', info: 'bg-blue-500/5 border-blue-500/20' };

function BoolCheck({ label, value, icon }: { label: string; value: boolean; icon: React.ReactNode }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition ${value ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
      <div className={`${value ? 'text-emerald-400' : 'text-red-400'}`}>{icon}</div>
      <span className="text-sm text-slate-300 flex-1">{label}</span>
      {value ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
    </div>
  );
}

function StatCard({ label, value, sub, icon }: { label: string; value: string | number; sub?: string; icon: React.ReactNode }) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2 text-slate-500">{icon}<span className="text-[10px] font-bold uppercase tracking-widest">{label}</span></div>
      <p className="text-2xl font-black text-white">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

interface Company {
  id: string;
  name: string;
  url: string;
  industry_tags: string[];
  cms_platform?: string;
  cms_url?: string;
  cms_api_key?: string;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', url: '', industry_tags: '' });
  const [loading, setLoading] = useState(false);
  const [scanningAll, setScanningAll] = useState(false);
  const [scores, setScores] = useState<Record<string, number | 'loading' | 'error'>>({});

  // Comprehensive SEO State
  const [scanResults, setScanResults] = useState<Record<string, any>>({});
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // AI Auto-Fix State
  const [aiFixing, setAiFixing] = useState<Record<string, boolean>>({});
  const [aiFixResults, setAiFixResults] = useState<Record<string, any>>({});

  // CMS Modal State
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [cmsModalCompany, setCmsModalCompany] = useState<Company | null>(null);
  const [cmsData, setCmsData] = useState({ cms_platform: 'none', cms_url: '', cms_api_key: '' });
  const [cmsLoading, setCmsLoading] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  // Implicit Auto-Scan after fetching companies!
  useEffect(() => {
    if (companies.length > 0 && Object.keys(scanResults).length === 0 && !scanningAll) {
      handleScanAll();
    }
  }, [companies]);

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
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: formData.name,
            url: formData.url,
            industry_tags: formData.industry_tags.split(',').map((t) => t.trim()),
          }),
        }
      );

      if (response.ok) {
        setFormData({ name: '', url: '', industry_tags: '' });
        setShowForm(false);
        await fetchCompanies();
      }
    } catch (error) {
      console.error('Failed to create company:', error);
    } finally {
      setLoading(false);
    }
  };



  const openCmsModal = (company: Company) => {
    setCmsModalCompany(company);
    setCmsData({
      cms_platform: company.cms_platform || 'none',
      cms_url: company.cms_url || '',
      cms_api_key: company.cms_api_key || ''
    });
  };

  const handleUpdateCms = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cmsModalCompany) return;
    setCmsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies/${cmsModalCompany.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cms_platform: cmsData.cms_platform,
          cms_url: cmsData.cms_url,
          cms_api_key: cmsData.cms_api_key,
        })
      });

      if (response.ok) {
        setCmsModalCompany(null);
        fetchCompanies();
      }
    } catch (err) {
      console.error(err);
      alert('Failed to update CMS options');
    } finally {
      setCmsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies/${id}`,
        {
          method: 'DELETE',
        }
      );

      if (response.ok) {
        await fetchCompanies();
      }
    } catch (error) {
      console.error('Failed to delete company:', error);
    }
  };

  const handleScanAll = async () => {
    if (companies.length === 0) return;
    setScanningAll(true);

    // We scan sequentially to avoid hitting rate limits or overwhelming the backend
    for (const company of companies) {
      if (scores[company.id] !== undefined && scores[company.id] !== 'error') continue; // skip already scanned items

      setScores((prev) => ({ ...prev, [company.id]: 'loading' }));
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/company/${company.id}`,
          { method: 'POST' }
        );
        if (!response.ok) throw new Error('Scan failed');
        const data = await response.json();
        setScores((prev) => ({ ...prev, [company.id]: data.seo_score }));
        setScanResults((prev) => ({ ...prev, [company.id]: data }));
      } catch (error) {
        setScores((prev) => ({ ...prev, [company.id]: 'error' }));
      }
    }

    setScanningAll(false);
    alert('✅ Completed parallel domain scan for all active companies.');
  };

  const handleSingleScan = async (company: any) => {
    setScores((prev) => ({ ...prev, [company.id]: 'loading' }));
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/company/${company.id}`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Scan failed');
      const data = await response.json();
      setScores((prev) => ({ ...prev, [company.id]: data.seo_score }));
      setScanResults((prev) => ({ ...prev, [company.id]: data }));
    } catch (error) {
      setScores((prev) => ({ ...prev, [company.id]: 'error' }));
      alert(`❌ Scan failed for ${company.name}. Check domain resolution.`);
    }
  };

  const handleAiFix = async (companyId: string) => {
    const payload = scanResults[companyId];
    if (!payload) return;

    setAiFixing((prev) => ({ ...prev, [companyId]: true }));
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/fix-seo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: companyId, scan_data: payload })
      });

      if (!response.ok) throw new Error('AI Fix failed');
      const data = await response.json();
      setAiFixResults((prev) => ({ ...prev, [companyId]: data }));
    } catch (err) {
      console.error(err);
      alert('Failed to generate AI fix.');
    } finally {
      setAiFixing((prev) => ({ ...prev, [companyId]: false }));
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">Companies</h1>
          <div className="flex gap-3">
            <button
              onClick={handleScanAll}
              disabled={scanningAll || companies.length === 0}
              className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg flex items-center gap-2 transition"
            >
              {scanningAll ? 'Scanning...' : 'Scan All SEO'}
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg"
            >
              {showForm ? 'Cancel' : '+ Add Company'}
            </button>
          </div>
        </div>

        {showForm && (
          <form
            onSubmit={handleSubmit}
            className="bg-slate-800 border border-slate-700 rounded-lg p-6 space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-slate-200 mb-1">
                Company Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white"
                placeholder="Company name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-200 mb-1">
                Website URL
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                required
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white"
                placeholder="https://example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-200 mb-1">
                Industry Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.industry_tags}
                onChange={(e) => setFormData({ ...formData, industry_tags: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white"
                placeholder="CLEANTECH, TECHNOLOGY, AI"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg"
            >
              {loading ? 'Creating...' : 'Add Company'}
            </button>
          </form>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-4 py-3 text-slate-400 font-medium">Name</th>
                <th className="px-4 py-3 text-slate-400 font-medium">URL</th>
                <th className="px-4 py-3 text-slate-400 font-medium hidden lg:table-cell">Tags</th>
                <th className="px-4 py-3 text-slate-400 font-medium whitespace-nowrap">Load (ms)</th>
                <th className="px-4 py-3 text-slate-400 font-medium text-center">Errors</th>
                <th className="px-4 py-3 text-slate-400 font-medium">SEO Score</th>
                <th className="px-4 py-3 text-slate-400 font-medium hidden md:table-cell">Setup</th>
                <th className="px-4 py-3 text-slate-400 font-medium whitespace-nowrap">Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((company) => {
                const results = scanResults[company.id];
                const isExpanded = expandedRow === company.id;

                return (
                  <React.Fragment key={company.id}>
                    <tr
                      className="border-b border-slate-700 hover:bg-slate-800/80 cursor-pointer transition-colors"
                      onClick={() => setExpandedRow(isExpanded ? null : company.id)}
                    >
                      <td className="px-4 py-3 text-white font-medium flex items-center gap-2">
                        <span className={`text-slate-400 transition-transform ${isExpanded ? 'text-fuchsia-400' : ''}`}>
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </span>
                        {company.name}
                      </td>
                      <td className="px-4 py-3">
                        <a
                          href={company.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-cyan-400 hover:text-cyan-300"
                        >
                          {company.url}
                        </a>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <div className="flex flex-wrap gap-1">
                          {company.industry_tags.map((tag) => (
                            <span
                              key={tag}
                              className="text-xs bg-slate-700 text-slate-200 px-2 py-1 rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {results ? (
                          <span className={`${results.load_time_ms > 1500 ? 'text-amber-400' : 'text-emerald-400'} font-semibold text-xs`}>
                            {results.load_time_ms}
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {results ? (
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${results.issues?.length > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                            {results.issues?.length || 0}
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {scores[company.id] === 'loading' ? (
                          <span className="text-yellow-400 text-xs font-semibold animate-pulse">Scanning...</span>
                        ) : scores[company.id] === 'error' ? (
                          <span className="text-red-400 text-xs font-semibold">Failed</span>
                        ) : typeof scores[company.id] === 'number' ? (
                          <span className={`px-2 py-1 rounded text-xs font-bold ${(scores[company.id] as number) >= 80 ? 'bg-emerald-500/10 text-emerald-400' :
                              (scores[company.id] as number) >= 60 ? 'bg-amber-500/10 text-amber-400' :
                                'bg-red-500/10 text-red-400'
                            }`}>
                            {scores[company.id]}/100
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        {results ? (
                          <div className="flex gap-2">
                            <span title="SSL" className={`flex items-center justify-center w-5 h-5 rounded-sm ${results.has_ssl ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-600'}`}>{results.has_ssl ? '✓' : '✗'}</span>
                            <span title="Sitemap" className={`flex items-center justify-center w-5 h-5 rounded-sm ${results.has_sitemap ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-600'}`}>{results.has_sitemap ? '✓' : '✗'}</span>
                            <span title="Robots.txt" className={`flex items-center justify-center w-5 h-5 rounded-sm ${results.has_robots_txt ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-600'}`}>{results.has_robots_txt ? '✓' : '✗'}</span>
                            <span title="Analytics" className={`flex items-center justify-center w-5 h-5 rounded-sm ${results.has_google_analytics ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-600'}`}>{results.has_google_analytics ? '✓' : '✗'}</span>
                          </div>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 flex gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => openCmsModal(company)}
                          className="text-slate-400 hover:text-fuchsia-400 transition"
                          title="CMS Integration Settings"
                        >
                          <Settings size={18} />
                        </button>
                        <button 
                          onClick={() => setEditingCompany(company)}
                          className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-900/30 rounded transition"
                          title="Manage / Edit Database Entry"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleSingleScan(company)}
                          className={`p-1.5 transition rounded ${scores[company.id] === 'loading' ? 'text-green-500 animate-spin cursor-not-allowed' : 'text-slate-400 hover:text-green-400 hover:bg-green-900/30'}`}
                          title="Single Re-scan"
                          disabled={scores[company.id] === 'loading'}
                        >
                          <Activity size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(company.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>

                    {/* EXPANDABLE SEO ROW */}
                    {isExpanded && results && (
                      <tr className="bg-slate-900 border-b border-slate-800">
                        <td colSpan={8} className="p-0">
                          <div className="p-6 border-l-4 border-fuchsia-500 animate-in slide-in-from-top-2">

                            {/* Auto-Fix Toolbar */}
                            <div className="flex items-center justify-between mb-6 bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                              <div>
                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                  <Activity size={20} className="text-fuchsia-400" />
                                  Technical Diagnostic Report
                                </h3>
                                <p className="text-sm text-slate-400 mt-1">Found {results.issues?.length || 0} critical problems with this property.</p>
                              </div>
                              <button
                                onClick={() => handleAiFix(company.id)}
                                disabled={aiFixing[company.id]}
                                className="bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 font-bold px-6 py-2.5 rounded-lg transition shadow-lg shadow-purple-500/20 flex items-center gap-2"
                              >
                                <Wand2 size={16} />
                                {aiFixing[company.id] ? 'Generating Fixes...' : '✨ Auto-Fix SEO'}
                              </button>
                            </div>

                            {/* AI Fix Results Rendering */}
                            {aiFixResults[company.id] && (
                              <div className="mb-6 bg-purple-900/20 border border-purple-500/30 rounded-xl p-5 animate-in fade-in">
                                <div className="flex items-center justify-between mb-4 border-b border-purple-500/30 pb-3">
                                  <h4 className="text-purple-300 font-bold flex items-center gap-2">
                                    <Wand2 size={18} /> Optimized SEO Output
                                  </h4>
                                  <button
                                    onClick={() => {
                                      const fix = aiFixResults[company.id];
                                      if (!fix) return;
                                      const text = `<!-- Generated by EX Venture -->\n<title>${fix.optimized_title}</title>\n<meta name="description" content="${fix.optimized_meta}" />`;
                                      navigator.clipboard.writeText(text);
                                      alert("Copied HTML Tags to clipboard!");
                                    }}
                                    className="bg-purple-600/80 hover:bg-purple-500 text-white text-xs font-bold px-4 py-1.5 rounded flex items-center gap-2 transition"
                                  >
                                    📋 Copy HTML Head Tags
                                  </button>
                                </div>
                                <div className="grid grid-cols-2 gap-6 mb-4">
                                  <div className="space-y-1">
                                    <label className="text-xs text-purple-400 font-bold uppercase tracking-wider">New Meta Title</label>
                                    <div className="flex gap-2">
                                      <input readOnly value={aiFixResults[company.id]?.optimized_title || ''} className="bg-slate-900 w-full rounded border border-slate-700 p-2 text-sm text-white" />
                                      <button onClick={() => navigator.clipboard.writeText(aiFixResults[company.id]?.optimized_title)} className="bg-slate-800 px-3 rounded hover:bg-slate-700 text-slate-300">Copy</button>
                                    </div>
                                  </div>
                                  <div className="space-y-1">
                                    <label className="text-xs text-purple-400 font-bold uppercase tracking-wider">New Meta Description</label>
                                    <div className="flex gap-2">
                                      <input readOnly value={aiFixResults[company.id]?.optimized_meta || ''} className="bg-slate-900 w-full rounded border border-slate-700 p-2 text-sm text-white" />
                                      <button onClick={() => navigator.clipboard.writeText(aiFixResults[company.id]?.optimized_meta)} className="bg-slate-800 px-3 rounded hover:bg-slate-700 text-slate-300">Copy</button>
                                    </div>
                                  </div>
                                </div>
                                <div>
                                  <label className="text-xs text-purple-400 font-bold uppercase tracking-wider block mb-2">Developer Action Plan</label>
                                  <div className="bg-slate-900 border border-slate-700 rounded p-4 text-sm text-slate-300 whitespace-pre-line">
                                    {aiFixResults[company.id]?.action_plan || 'No actions required.'}
                                  </div>
                                </div>
                              </div>
                            )}

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                              <StatCard label="Load Time" value={`${results.load_time_ms}ms`} sub={results.load_time_ms < 1500 ? 'Fast' : results.load_time_ms < 3000 ? 'Moderate' : 'Slow'} icon={<Clock className="w-3.5 h-3.5" />} />
                              <StatCard label="Words" value={results.word_count?.toLocaleString() || 0} sub={`${results.text_to_html_ratio}% text ratio`} icon={<FileText className="w-3.5 h-3.5" />} />
                              <StatCard label="Images" value={results.total_images || 0} sub={`${results.images_without_alt} missing alt`} icon={<Image className="w-3.5 h-3.5" />} />
                              <StatCard label="Links" value={(results.internal_links || 0) + (results.external_links || 0)} sub={`${results.internal_links} int · ${results.external_links} ext`} icon={<Link2 className="w-3.5 h-3.5" />} />
                            </div>

                            <div className="grid md:grid-cols-2 gap-6 mb-6">
                              <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
                                <div className="flex items-center justify-between mb-4">
                                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                                    <ShieldAlert className="w-5 h-5 text-red-400" /> Issues Found
                                  </h3>
                                </div>
                                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                  {results.issues?.length === 0 ? (
                                    <p className="text-sm text-emerald-400 py-4 text-center">No issues found — perfect score!</p>
                                  ) : (
                                    results.issues?.map((issue: any, i: number) => (
                                      <div key={i} className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border ${SEV_BG[issue.severity as keyof typeof SEV_BG] || SEV_BG['info']}`}>
                                        {SEV_ICON[issue.severity as keyof typeof SEV_ICON] || SEV_ICON['info']}
                                        <span className="text-sm text-slate-300">{issue.message}</span>
                                      </div>
                                    ))
                                  )}
                                </div>
                              </div>

                              <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
                                <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
                                  <ShieldCheck className="w-5 h-5 text-emerald-400" /> Checks Passed
                                  <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full font-bold ml-auto">{results.passes?.length || 0}</span>
                                </h3>
                                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                  {results.passes?.map((pass: string, i: number) => (
                                    <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
                                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                                      <span className="text-sm text-slate-300">{pass}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>

                            <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
                              <h3 className="text-base font-bold text-white flex items-center gap-2 mb-5">
                                <Shield className="w-5 h-5 text-blue-400" /> Core Environment Sensors
                              </h3>
                              <div className="grid sm:grid-cols-3 gap-3 flex-wrap">
                                <BoolCheck label="HTTPS / SSL" value={results.has_ssl} icon={<Lock className="w-4 h-4" />} />
                                <BoolCheck label="Mobile Viewport" value={results.has_viewport} icon={<Smartphone className="w-4 h-4" />} />
                                <BoolCheck label="robots.txt" value={results.has_robots_txt} icon={<FileCode className="w-4 h-4" />} />
                                <BoolCheck label="sitemap.xml" value={results.has_sitemap} icon={<MapPin className="w-4 h-4" />} />
                                <BoolCheck label="Open Graph Tags" value={results.has_og_tags} icon={<Share2 className="w-4 h-4" />} />
                                <BoolCheck label="Schema Structure" value={results.has_schema_markup} icon={<Code className="w-4 h-4" />} />
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {companies.length === 0 && (
          <div className="text-center text-slate-400 py-8">No companies yet</div>
        )}
      </div>

      {cmsModalCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Globe className="w-5 h-5 text-fuchsia-400" />
                CMS Settings
              </h3>
              <button onClick={() => setCmsModalCompany(null)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateCms} className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Publishing Platform</label>
                <div className="grid grid-cols-3 gap-3">
                  {['none', 'wordpress', 'webhook'].map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setCmsData({ ...cmsData, cms_platform: type })}
                      className={`py-2 px-3 rounded-lg text-sm font-bold border transition ${cmsData.cms_platform === type
                          ? 'bg-fuchsia-600/20 border-fuchsia-500 text-fuchsia-300'
                          : 'bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-600'
                        }`}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {cmsData.cms_platform !== 'none' && (
                <div className="space-y-4 animate-in slide-in-from-top-2">
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <Globe className="w-4 h-4 text-slate-500" /> Connection URL
                    </label>
                    <input
                      type="url"
                      value={cmsData.cms_url}
                      onChange={(e) => setCmsData({ ...cmsData, cms_url: e.target.value })}
                      placeholder="https://company.com/wp-json"
                      required
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <Key className="w-4 h-4 text-slate-500" /> App Password / API Key
                    </label>
                    <input
                      type="password"
                      value={cmsData.cms_api_key}
                      onChange={(e) => setCmsData({ ...cmsData, cms_api_key: e.target.value })}
                      placeholder="Username:ApplicationPassword (if WP)"
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500 transition"
                    />
                  </div>
                  <p className="text-xs text-slate-500">
                    {cmsData.cms_platform === 'wordpress'
                      ? 'Format your key as "username:password" using WordPress Application Passwords.'
                      : 'Not all webhooks require an API key to be sent. Leave blank if open.'}
                  </p>
                </div>
              )}

              <div className="flex justify-end pt-4 border-t border-slate-800 mt-6">
                <button
                  type="submit"
                  disabled={cmsLoading}
                  className="bg-fuchsia-600 hover:bg-fuchsia-500 disabled:opacity-50 text-white font-bold px-6 py-2.5 rounded-lg shadow-lg flex items-center gap-2 transition"
                >
                  {cmsLoading ? 'Saving...' : 'Save Integration'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Actual Manage / Edit Modal */}
      {editingCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Edit2 className="text-blue-400" size={20} /> Manage Company
              </h2>
              <button onClick={() => setEditingCompany(null)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Company Name</label>
                <input 
                  type="text" 
                  value={editingCompany.name} 
                  readOnly
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white opacity-50 cursor-not-allowed" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Company URL</label>
                <input 
                  type="text" 
                  value={editingCompany.url} 
                  readOnly
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white opacity-50 cursor-not-allowed" 
                />
              </div>
              <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                <AlertCircle size={14} /> Full DB mutability requires advanced SaaS authorization keys.
              </p>
            </div>
            
            <button
              onClick={() => setEditingCompany(null)}
              className="mt-6 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition"
            >
              Save & Close
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}
