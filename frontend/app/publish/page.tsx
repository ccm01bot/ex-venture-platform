'use client';

import React from 'react';
import Layout from '@/components/Layout';

export default function PublishPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Article Management</h1>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <StatCard label="Total Articles" value="0" />
          <StatCard label="Published" value="0" />
          <StatCard label="Drafts" value="0" />
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
          <p className="text-slate-400 mb-4">No articles yet</p>
          <a
            href="/companies"
            className="inline-block bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg"
          >
            Create Your First Article
          </a>
        </div>
      </div>
    </Layout>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <p className="text-slate-400 text-sm">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  );
}
