import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Sparkles, Megaphone, Users, ListFilter } from 'lucide-react';

export default function OutreachTabs({ currentTab }: { currentTab: string }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', href: '/outreach', icon: <LayoutDashboard size={18} /> },
    { id: 'agent', label: 'AI Lead Agent', href: '/outreach/agent', icon: <Sparkles size={18} /> },
    { id: 'campaigns', label: 'Campaigns', href: '/outreach/campaigns', icon: <Megaphone size={18} /> },
    { id: 'contacts', label: 'Contacts', href: '/outreach/contacts', icon: <Users size={18} /> },
    { id: 'media', label: 'Media Lists', href: '/outreach/media-lists', icon: <ListFilter size={18} /> },
  ];

  return (
    <div className="flex items-center gap-2 border-b border-slate-800 pb-px mb-8 overflow-x-auto">
      {tabs.map((tab) => (
        <Link
          key={tab.id}
          href={tab.href}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            currentTab === tab.id
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
          }`}
        >
          {tab.icon}
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
