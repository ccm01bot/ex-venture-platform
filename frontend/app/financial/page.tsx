'use client';

import React from 'react';
import Layout from '@/components/Layout';

export default function FinancialPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Financial Overview</h1>

        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total Balance" value="$0.00" />
          <StatCard label="Accounts" value="0" />
          <StatCard label="This Month" value="$0.00" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <QuickLink title="Accounts" href="/financial/accounts" />
          <QuickLink title="Transactions" href="/financial/transactions" />
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
      className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-cyan-500 text-center transition"
    >
      <p className="text-white font-semibold">{title}</p>
    </a>
  );
}
