'use client';

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import {
  Search, Globe, Shield, ShieldCheck, ShieldAlert, ShieldX, AlertTriangle, CheckCircle2,
  XCircle, Info, Clock, FileText, Image, Link2, Code, Type, Smartphone,
  Lock, FileCode, MapPin, Share2, BarChart3, ChevronDown, Loader2, ExternalLink, Zap
} from 'lucide-react';

type Severity = 'critical' | 'warning' | 'info';
interface Issue { severity: Severity; message: string; }
interface ScanData {
  url: string; status_code: number; load_time_ms: number;
  title: string | null; title_length: number;
  meta_description: string | null; meta_description_length: number;
  canonical: string | null; language: string | null;
  h1_tags: string[]; h2_tags: string[]; h3_tags: string[]; heading_count: number;
  word_count: number; text_to_html_ratio: number;
  total_images: number; images_without_alt: number; image_details: any[];
  internal_links: number; external_links: number;
  has_ssl: boolean; has_viewport: boolean; has_robots_txt: boolean;
  has_sitemap: boolean; has_og_tags: boolean; has_twitter_cards: boolean;
  has_schema_markup: boolean; has_google_analytics: boolean; has_favicon: boolean;
  total_page_size_kb: number;
  inline_css_count: number; inline_js_count: number;
  external_css_count: number; external_js_count: number;
  og_title: string | null; og_description: string | null; og_image: string | null;
  twitter_card: string | null; charset: string | null;
  seo_score: number; issues: Issue[]; passes: string[];
}

const SCORE_COLOR = (s: number) =>
  s >= 80 ? 'text-emerald-400' : s >= 60 ? 'text-amber-400' : s >= 40 ? 'text-orange-400' : 'text-red-400';
const SCORE_BG = (s: number) =>
  s >= 80 ? 'from-emerald-500 to-emerald-600' : s >= 60 ? 'from-amber-500 to-amber-600' : s >= 40 ? 'from-orange-500 to-orange-600' : 'from-red-500 to-red-600';
const SCORE_RING = (s: number) =>
  s >= 80 ? 'ring-emerald-500/30' : s >= 60 ? 'ring-amber-500/30' : s >= 40 ? 'ring-orange-500/30' : 'ring-red-500/30';
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

function ScanBlock({ company }: { company: any }) {
  const [data, setData] = useState<ScanData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchLatest = async () => {
      try {
        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/company/${company.id}/latest`);
        if (resp.ok && isMounted) {
          const result = await resp.json();
          setData(result);
        }
      } catch (err) {
        // silent fail to null, will show 'Run Initial Scan' button
        console.error("No cached scan");
      }
    };
    fetchLatest();
    return () => { isMounted = false; };
  }, [company.id]);

  const handleForceScan = async () => {
    if (loading) return; 
    setLoading(true);
    setError('');
    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scan/company/${company.id}`, {
        method: 'POST',
      });
      if (!resp.ok) throw new Error(`Server error ${resp.status}`);
      const result = await resp.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Scan failed');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  const displayScore = data ? data.seo_score : '—';
  const displayStatus = data ? data.status_code : 'N/A';

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden mb-8 shadow-xl transition-all">
      <div
        onClick={handleToggle}
        className="bg-gradient-to-r hover:from-slate-800 hover:to-slate-800/80 from-slate-800/50 to-slate-900/50 px-8 py-5 border-b border-slate-700/50 flex items-center justify-between cursor-pointer group transition-colors"
      >
        <div>
          <h2 className="text-2xl font-black text-white flex items-center gap-3">
            <Globe className={`w-6 h-6 transition-colors ${expanded ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'}`} /> {company.name}
          </h2>
          <a href={company.url} onClick={(e) => e.stopPropagation()} target="_blank" rel="noopener noreferrer" className="text-sm text-cyan-400/70 hover:text-cyan-300 transition flex items-center gap-1 mt-1">
            <ExternalLink className="w-4 h-4" /> {company.url}
          </a>
        </div>
        <div className="flex items-center gap-6">
          {loading ? (
            <div className="text-right flex items-center gap-3">
              <span className="text-sm text-cyan-400 font-medium">Scanning Array...</span>
              <Loader2 className="w-6 h-6 text-cyan-500 animate-spin" />
            </div>
          ) : (
            <>
              <div className="text-right hidden sm:block">
                <p className="text-xs text-slate-400 uppercase font-bold tracking-wider">Status</p>
                <p className={`text-lg font-mono ${data && data.status_code === 200 ? 'text-emerald-400' : 'text-slate-500'}`}>{displayStatus}</p>
              </div>
              <div className={`w-16 h-16 rounded-full ring-4 ${data ? SCORE_RING(displayScore as number) : 'ring-slate-700/50'} flex items-center justify-center bg-gradient-to-br ${data ? SCORE_BG(displayScore as number) : 'from-slate-800 to-slate-900'} shadow-lg`}>
                <span className="text-xl font-black text-white">{displayScore}</span>
              </div>
              <ChevronDown className={`w-6 h-6 text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`} />
            </>
          )}
        </div>
      </div>

      {expanded && (
        <div className="p-8 space-y-6 animate-in slide-in-from-top-2">
          {loading && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 animate-pulse text-center space-y-4">
              <Loader2 className="w-8 h-8 text-cyan-500 animate-spin mx-auto" />
              <p className="text-slate-400">Auditing Technical Metrics Live...</p>
            </div>
          )}

          {error && !loading && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6">
              <p className="text-red-400 text-sm flex items-center gap-2"><XCircle className="w-4 h-4" /> {error || "Scan failed"}</p>
            </div>
          )}

          {!data && !loading && !error && (
            <div className="text-center py-10 bg-slate-900/40 rounded-xl border border-slate-800">
               <Globe className="w-10 h-10 text-slate-600 mx-auto mb-4" />
               <p className="text-slate-400 mb-6">This company has no historical SEO scan cached in the database.</p>
               <button onClick={handleForceScan} className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2.5 rounded-lg shadow-lg shadow-cyan-500/20 transition flex items-center gap-2 mx-auto font-bold">
                 <Search className="w-4 h-4" /> Run Initial Scan
               </button>
            </div>
          )}

          {data && !loading && (
            <>
              <div className="flex justify-end p-2 -mt-4 border-b border-slate-800/60 pb-6 mb-6">
                 <button onClick={handleForceScan} className="text-xs font-bold px-4 py-2 bg-slate-800 hover:bg-cyan-900/40 text-slate-300 hover:text-cyan-400 border border-slate-700 transition rounded-lg flex items-center gap-2">
                    <Search className="w-3.5 h-3.5" /> Force Rescan Cache
                 </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Load Time" value={`${data.load_time_ms}ms`} sub={data.load_time_ms < 1500 ? 'Fast' : data.load_time_ms < 3000 ? 'Moderate' : 'Slow'} icon={<Clock className="w-3.5 h-3.5" />} />
                <StatCard label="Words" value={data.word_count.toLocaleString()} sub={`${data.text_to_html_ratio}% text ratio`} icon={<FileText className="w-3.5 h-3.5" />} />
                <StatCard label="Images" value={data.total_images} sub={`${data.images_without_alt} missing alt`} icon={<Image className="w-3.5 h-3.5" />} />
                <StatCard label="Links" value={data.internal_links + data.external_links} sub={`${data.internal_links} int · ${data.external_links} ext`} icon={<Link2 className="w-3.5 h-3.5" />} />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5 text-red-400" /> Issues Found
                    </h3>
                  </div>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    {data.issues.length === 0 ? (
                      <p className="text-sm text-emerald-400 py-4 text-center">No issues found — perfect score!</p>
                    ) : (
                      data.issues.map((issue, i) => (
                        <div key={i} className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border ${SEV_BG[issue.severity]}`}>
                          {SEV_ICON[issue.severity]}
                          <span className="text-sm text-slate-300">{issue.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
                  <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
                    <ShieldCheck className="w-5 h-5 text-emerald-400" /> Checks Passed
                    <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full font-bold ml-auto">{data.passes.length}</span>
                  </h3>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    {data.passes.map((pass, i) => (
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
                  <BoolCheck label="HTTPS / SSL" value={data.has_ssl} icon={<Lock className="w-4 h-4" />} />
                  <BoolCheck label="Mobile Viewport" value={data.has_viewport} icon={<Smartphone className="w-4 h-4" />} />
                  <BoolCheck label="robots.txt" value={data.has_robots_txt} icon={<FileCode className="w-4 h-4" />} />
                  <BoolCheck label="sitemap.xml" value={data.has_sitemap} icon={<MapPin className="w-4 h-4" />} />
                  <BoolCheck label="Open Graph Tags" value={data.has_og_tags} icon={<Share2 className="w-4 h-4" />} />
                  <BoolCheck label="Schema Structure" value={data.has_schema_markup} icon={<Code className="w-4 h-4" />} />
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function ScanPage() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies`);
        if (resp.ok) {
          const result = await resp.json();
          setCompanies(result);
        }
      } catch (err) {
        console.error("Failed to load companies mapping");
      } finally {
        setLoadingCompanies(false);
      }
    };
    fetchCompanies();
  }, []);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8 pb-20">

        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-slate-800 p-8 md:p-12 mb-10">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-[80px]" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-fuchsia-500/5 rounded-full blur-[60px]" />

          <div className="relative z-10">
            <h1 className="text-3xl md:text-4xl font-black text-white mb-2 flex items-center gap-3">
              <Search className="w-8 h-8 text-cyan-400" /> Active Database Scan
            </h1>
            <p className="text-slate-400 max-w-xl">
              This module automatically imports all active endpoints directly from your dashboard configuration and systematically performs rigorous technical data auditing per domain parameter.
            </p>
          </div>
        </div>

        {loadingCompanies ? (
          <div className="text-center py-20 animate-pulse">
            <Loader2 className="w-12 h-12 text-cyan-500 animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white">Importing Dashboard Companies...</h3>
          </div>
        ) : companies.length > 0 ? (
          <div className="space-y-6">
            {companies.map(company => (
              <ScanBlock key={company.id} company={company} />
            ))}
          </div>
        ) : (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center">
            <Globe className="w-12 h-12 text-slate-500 mb-4 mx-auto" />
            <h2 className="text-xl font-bold text-white mb-2">No Companies Found in Dashboard</h2>
            <p className="text-slate-400">Please go back to the Companies dashboard and input a valid endpoint url first.</p>
          </div>
        )}

      </div>
    </Layout>
  );
}
