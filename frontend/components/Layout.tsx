'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3 } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#070b14] relative overflow-hidden text-slate-100 font-sans">
      {/* Global Ambient Glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-900/20 blur-[120px] pointer-events-none mix-blend-screen" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-fuchsia-900/20 blur-[120px] pointer-events-none mix-blend-screen" />

      {/* Sidebar */}
      <div className="fixed left-0 top-0 w-64 h-screen bg-slate-950/40 backdrop-blur-3xl border-r border-slate-800/60 flex flex-col overflow-y-auto z-50 shadow-2xl">
        <div className="p-6 border-b border-slate-800/60 bg-gradient-to-r from-transparent to-slate-900/50">
          <Link href="/" className="flex items-center gap-3 transition hover:scale-105 duration-300">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.4)]">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400">EX Venture</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <NavItem href="/" label="Home" currentPath={pathname} />
          <NavItem href="/dashboard" label="Dashboard" currentPath={pathname} />
          
          <div className="pt-6 pb-2">
            <p className="px-3 text-[10px] font-black text-fuchsia-400/80 uppercase tracking-widest mb-3">Portfolio Mgmt</p>
            <div className="space-y-1">
              <NavItem href="/companies" label="Companies" currentPath={pathname} />
              <NavItem href="/scan" label="Scan All" currentPath={pathname} />
              <NavItem href="/youtube-seo" label="YouTube SEO" currentPath={pathname} />
              <NavItem href="/article-generation" label="Article Gen" currentPath={pathname} />
              <NavItem href="/personal-brand" label="Personal Brand" currentPath={pathname} />
              <NavItem href="/outreach/agent" label="AI Lead Agent" currentPath={pathname} />
              <NavItem href="/reports" label="Reports" currentPath={pathname} />
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-slate-800/60 bg-slate-900/20">
          <NavItem href="/settings" label="Settings" currentPath={pathname} />
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8 min-h-screen relative z-10 w-[calc(100%-16rem)]">
        <div className="max-w-7xl mx-auto">{children}</div>
      </div>
    </div>
  );
}

function NavItem({ href, label, currentPath }: { href: string; label: string; currentPath: string | null }) {
  const isActive = currentPath === href || (href !== '/' && currentPath?.startsWith(href));
  
  return (
    <Link
      href={href}
      className={`block px-3 py-2 text-sm rounded-lg transition-all duration-300 ${
        isActive 
          ? 'bg-cyan-500/10 text-cyan-400 font-semibold shadow-[inset_2px_0_0_rgba(6,182,212,1)]' 
          : 'text-slate-400 hover:text-white hover:bg-slate-800/80 hover:translate-x-1'
      }`}
    >
      {label}
    </Link>
  );
}
