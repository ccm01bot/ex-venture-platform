'use client';

import React from 'react';
import Layout from '@/components/Layout';

export default function ScanPage() {
  const handleScanAll = () => {
    alert('Starting portfolio scan...');
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-cyan-600 to-fuchsia-600 rounded-lg p-12 text-center">
          <h1 className="text-4xl font-bold text-white mb-2">Ready to Scan</h1>
          <p className="text-lg text-cyan-100 mb-8">
            Scan all companies for SEO issues and compliance
          </p>
          <button
            onClick={handleScanAll}
            className="bg-white text-cyan-600 hover:bg-cyan-50 font-bold px-8 py-3 rounded-lg transition"
          >
            Scan All Companies
          </button>
        </div>

        {/* Scan Methodology Criteria */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white">Scan Methodology & Criteria</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 pointer-events-none">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-xl mb-4">1</div>
              <h3 className="text-white font-bold mb-4">Technical SEO</h3>
              <ul className="text-slate-400 text-sm space-y-2">
                <li className="flex gap-2"><span>•</span> Core Web Vitals passing status</li>
                <li className="flex gap-2"><span>•</span> Mobile-responsive viewport tags</li>
                <li className="flex gap-2"><span>•</span> SSL configuration validity</li>
                <li className="flex gap-2"><span>•</span> robots.txt & sitemap.xml parsability</li>
                <li className="flex gap-2"><span>•</span> Status code validation (detect 404s/5xx)</li>
              </ul>
            </div>
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 pointer-events-none">
              <div className="w-10 h-10 rounded-lg bg-fuchsia-500/10 text-fuchsia-400 flex items-center justify-center font-bold text-xl mb-4">2</div>
              <h3 className="text-white font-bold mb-4">On-Page Logic</h3>
              <ul className="text-slate-400 text-sm space-y-2">
                <li className="flex gap-2"><span>•</span> Meta title & description lengths</li>
                <li className="flex gap-2"><span>•</span> Exact strict H1-H6 structural hierarchy</li>
                <li className="flex gap-2"><span>•</span> Target keyword density & prominence</li>
                <li className="flex gap-2"><span>•</span> URL slug optimization</li>
                <li className="flex gap-2"><span>•</span> Canonical tag definitions</li>
              </ul>
            </div>
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 pointer-events-none">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-xl mb-4">3</div>
              <h3 className="text-white font-bold mb-4">Content Quality</h3>
              <ul className="text-slate-400 text-sm space-y-2">
                <li className="flex gap-2"><span>•</span> Text-to-HTML ratio thresholds</li>
                <li className="flex gap-2"><span>•</span> Duplicate internal content detection</li>
                <li className="flex gap-2"><span>•</span> Flesch-Kincaid Readability scoring</li>
                <li className="flex gap-2"><span>•</span> Image ALT text completeness</li>
                <li className="flex gap-2"><span>•</span> Semantic depth & topical clusters</li>
              </ul>
            </div>
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 pointer-events-none">
              <div className="w-10 h-10 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-xl mb-4">4</div>
              <h3 className="text-white font-bold mb-4">Off-Page & Links</h3>
              <ul className="text-slate-400 text-sm space-y-2">
                <li className="flex gap-2"><span>•</span> Inbound backlink profile tracking</li>
                <li className="flex gap-2"><span>•</span> Toxic referring domain detection</li>
                <li className="flex gap-2"><span>•</span> Internal link density & orphaned pages</li>
                <li className="flex gap-2"><span>•</span> Dofollow vs Nofollow ratio balancing</li>
                <li className="flex gap-2"><span>•</span> Domain authority metrics</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white">Company Status</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="text-center text-slate-400 py-8">
              No companies to scan
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
