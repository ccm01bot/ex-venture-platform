'use client';

import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Trash2, Edit2 } from 'lucide-react';

interface Company {
  id: string;
  name: string;
  url: string;
  industry_tags: string[];
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', url: '', industry_tags: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/companies`
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
        `${process.env.NEXT_PUBLIC_API_URL}/api/companies`,
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

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/companies/${id}`,
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

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">Companies</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg"
          >
            {showForm ? 'Cancel' : '+ Add Company'}
          </button>
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
                <th className="px-4 py-3 text-slate-400 font-medium">Tags</th>
                <th className="px-4 py-3 text-slate-400 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((company) => (
                <tr key={company.id} className="border-b border-slate-700 hover:bg-slate-800/50">
                  <td className="px-4 py-3 text-white">{company.name}</td>
                  <td className="px-4 py-3">
                    <a
                      href={company.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300"
                    >
                      {company.url}
                    </a>
                  </td>
                  <td className="px-4 py-3">
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
                  <td className="px-4 py-3 flex gap-2">
                    <button className="text-cyan-400 hover:text-cyan-300">
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(company.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {companies.length === 0 && (
          <div className="text-center text-slate-400 py-8">No companies yet</div>
        )}
      </div>
    </Layout>
  );
}
