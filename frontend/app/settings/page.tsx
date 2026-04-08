'use client';

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import { User, Key, Bell, CreditCard, Save, Shield } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <Layout>
      <div className="space-y-8 max-w-6xl mx-auto">
        <div className="border-b border-slate-800 pb-6">
          <h1 className="text-3xl font-extrabold text-white">Platform Settings</h1>
          <p className="text-slate-400 mt-1">Manage your account preferences, API integrations, and security.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Settings Sidebar Nav */}
          <div className="md:col-span-1 space-y-2">
            <button 
              onClick={() => setActiveTab('profile')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeTab === 'profile' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
            >
              <User size={18} /> Profile Info
            </button>
            <button 
              onClick={() => setActiveTab('api')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeTab === 'api' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
            >
              <Key size={18} /> API Keys
            </button>
            <button 
              onClick={() => setActiveTab('billing')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeTab === 'billing' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
            >
              <CreditCard size={18} /> Billing
            </button>
            <button 
              onClick={() => setActiveTab('notifications')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${activeTab === 'notifications' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'}`}
            >
              <Bell size={18} /> Notifications
            </button>
          </div>

          {/* Settings Content Area */}
          <div className="md:col-span-3">
            {activeTab === 'profile' && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-20 h-20 rounded-full bg-slate-800 border-2 border-slate-700 flex items-center justify-center text-3xl font-bold text-slate-500">
                    A
                  </div>
                  <button className="bg-slate-800 hover:bg-slate-700 text-white font-medium px-4 py-2 rounded-lg transition-colors border border-slate-700">
                    Change Avatar
                  </button>
                </div>
                
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-slate-300 mb-2">First Name</label>
                      <input type="text" defaultValue="Admin" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-slate-300 mb-2">Last Name</label>
                      <input type="text" defaultValue="User" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">Email Address</label>
                    <input type="email" defaultValue="admin@ex-venture.com" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-500 outline-none" disabled />
                    <p className="text-xs text-slate-500 mt-2">Email address cannot be changed directly. Contact support.</p>
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-800 flex justify-end">
                  <button className="bg-gradient-to-r from-cyan-600 to-fuchsia-600 hover:from-cyan-500 hover:to-fuchsia-500 text-white font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20">
                    <Save size={18} /> Save Changes
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'api' && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="flex items-center gap-3 mb-6">
                  <Shield className="text-cyan-400" size={24} />
                  <h2 className="text-xl font-bold text-white">External LLM Integrations</h2>
                </div>
                <p className="text-slate-400 text-sm mb-8">Supply your own API keys to interact with the underlying deep learning models for Content & Outreach generation. Keys are stored locally.</p>
                
                <div className="space-y-6">
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500"></div>
                    <label className="block text-sm font-bold text-white mb-1">Anthropic (Claude) API Key</label>
                    <p className="text-xs text-slate-500 mb-3">Required for YouTube SEO & Automated Outreach Agent.</p>
                    <input type="password" placeholder="sk-ant-api03-..." className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none" />
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-fuchsia-500"></div>
                    <label className="block text-sm font-bold text-white mb-1">OpenAI (DALL-E 3) API Key</label>
                    <p className="text-xs text-slate-500 mb-3">Required for Article Thumbnail generation & Image Generation.</p>
                    <input type="password" placeholder="sk-proj-..." className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-sm focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500 outline-none" />
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-800 flex justify-end">
                  <button className="bg-slate-800 hover:bg-slate-700 text-white font-bold px-6 py-3 rounded-xl transition-all border border-slate-600 flex items-center gap-2">
                    <Save size={18} /> Update Keys
                  </button>
                </div>
              </div>
            )}

            {(activeTab === 'billing' || activeTab === 'notifications') && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-16 text-center shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="w-16 h-16 rounded-full bg-slate-800 mx-auto flex items-center justify-center text-slate-500 mb-4">
                  {activeTab === 'billing' ? <CreditCard size={32} /> : <Bell size={32} />}
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Configure {activeTab === 'billing' ? 'Billing' : 'Notifications'}</h3>
                <p className="text-slate-400 max-w-sm mx-auto">This module is currently being managed manually via your enterprise contract representative.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
