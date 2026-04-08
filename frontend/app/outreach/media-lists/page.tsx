'use client';

import React from 'react';
import Layout from '@/components/Layout';
import OutreachTabs from '@/components/OutreachTabs';

export default function OutreachMediaListsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white mb-2">Outreach Hub</h1>
        <OutreachTabs currentTab="media" />
        
        <div className="mt-4">
           {/* Empty state since database was truncated */}
           <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
             <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 text-cyan-400 mb-4">
               <span className="text-2xl">📰</span>
             </div>
             <h3 className="text-xl font-bold text-white mb-2">No Media Lists Configured</h3>
             <p className="text-slate-400 mb-6 max-w-md mx-auto">Group your journalists, VC contacts, and influencers into targeted segments so you can run parallel press campaigns flawlessly.</p>
             <button className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-3 px-6 rounded-lg transition-colors shadow-lg">
               + Create Media List Segment
             </button>
           </div>
        </div>
      </div>
    </Layout>
  );
}
