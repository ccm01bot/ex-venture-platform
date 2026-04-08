'use client';

import React from 'react';
import Layout from '@/components/Layout';

export default function YouTubeAnalyticsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">YouTube Analytics</h1>
          <button className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg">
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-5 gap-4">
          <StatCard label="Subscribers" value="0" />
          <StatCard label="Total Views" value="0" />
          <StatCard label="Videos" value="0" />
          <StatCard label="Avg Views" value="0" />
          <StatCard label="Est. Daily" value="0" />
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-bold text-white mb-4">No channel connected</h2>
          <p className="text-slate-400 mb-4">
            Connect your YouTube channel to view analytics
          </p>
          <button className="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg">
            Connect Channel
          </button>
        </div>
      </div>
    </Layout>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <p className="text-slate-400 text-sm">{label}</p>
      <p className="text-xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}
