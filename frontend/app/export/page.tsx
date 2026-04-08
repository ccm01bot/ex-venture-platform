'use client';

import React from 'react';
import Layout from '@/components/Layout';

export default function ExportPage() {
  const handleDownloadCSV = () => {
    // In real implementation, would fetch actual data from API
    alert('CSV export would be generated here');
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Export Data</h1>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-2">CSV Report</h2>
            <p className="text-slate-400 text-sm mb-4">
              Download all scores, compliance, and issue counts
            </p>
            <button
              onClick={handleDownloadCSV}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg"
            >
              Download CSV
            </button>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-2">PDF Report</h2>
            <p className="text-slate-400 text-sm mb-4">Download detailed PDF report</p>
            <button
              disabled
              className="bg-slate-700 text-slate-400 font-medium px-4 py-2 rounded-lg cursor-not-allowed"
            >
              Coming Soon
            </button>
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Data Preview</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="px-4 py-3 text-slate-400">Company</th>
                  <th className="px-4 py-3 text-slate-400">Overall</th>
                  <th className="px-4 py-3 text-slate-400">Meta</th>
                  <th className="px-4 py-3 text-slate-400">Content</th>
                  <th className="px-4 py-3 text-slate-400">Technical</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-700">
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                    No data available
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
}
