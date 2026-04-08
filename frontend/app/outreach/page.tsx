'use client';

import React from 'react';
import Layout from '@/components/Layout';
import OutreachTabs from '@/components/OutreachTabs';

export default function OutreachPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white mb-2">Outreach Hub</h1>
        <OutreachTabs currentTab="dashboard" />
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Total Contacts" value="0" />
          <StatCard label="Active Campaigns" value="0" />
          <StatCard label="Messages Sent" value="0" />
          <StatCard label="Average Reply Rate" value="0%" />
        </div>

        <div className="grid grid-cols-4 gap-4">
          <QuickLink title="AI Lead Agent" href="/outreach/agent" />
          <QuickLink title="View Campaigns" href="/outreach/campaigns" />
          <QuickLink title="Manage Contacts" href="/outreach/contacts" />
          <QuickLink title="Media Lists" href="/outreach/media-lists" />
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

function QuickLink({ title, href }: { title: string; href: string }) {
  return (
    <a
      href={href}
      className={`bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-cyan-500 text-center transition ${title.includes('AI') ? 'border-fuchsia-500/50 shadow-lg shadow-fuchsia-500/10' : ''}`}
    >
      <p className="text-white font-semibold flex items-center justify-center gap-2">
        {title.includes('AI') && <span className="text-fuchsia-400">✧</span>}
        {title}
      </p>
    </a>
  );
}
