'use client';
import React, { useState } from 'react';
import Layout from '@/components/Layout';
import { Mic, Linkedin, Twitter, PenTool, Send } from 'lucide-react';

export default function PersonalBrandPage() {
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{ linkedin?: string; twitter?: string[]; article?: string } | null>(null);
  
  // Status states for auto-publishing
  const [publishStatus, setPublishStatus] = useState<{li?: string, tw?: string, ar?: string}>({});

  const generateContent = async () => {
    if (!transcript) return;
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/executive/ghostwriter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript }),
      });
      const data = await res.json();
      setResults(data);
      setPublishStatus({}); // Reset publish state
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = (platform: 'li'|'tw'|'ar') => {
    setPublishStatus(prev => ({...prev, [platform]: 'publishing'}));
    setTimeout(() => {
      setPublishStatus(prev => ({...prev, [platform]: 'success'}));
    }, 1500);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Personal Brand Ghostwriter</h1>
        
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 bg-slate-900 border border-slate-700 rounded-full flex items-center justify-center mb-4">
              <Mic className="w-6 h-6 text-cyan-400" />
            </div>
            <h2 className="text-xl font-bold text-slate-100 mb-2">Voice-to-LinkedIn Engine</h2>
            <p className="text-slate-400 max-w-xl mx-auto text-center text-sm">
              Input your raw transcribed thoughts. The AI structuralizes it into viral LinkedIn posts, Twitter threads, and long-form articles. Approve and auto-publish instantly.
            </p>
          </div>
          
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            className="w-full h-32 bg-slate-900 border border-slate-700 rounded-lg p-4 text-white focus:outline-none focus:border-cyan-500 mb-4"
            placeholder="Dictate your raw thoughts here (e.g. 'I was thinking about how AI automation isn't taking jobs but just increasing capital velocity...')"
          />

          <div className="flex justify-center">
            <button 
              onClick={generateContent}
              disabled={loading || !transcript}
              className="bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3 rounded-full font-bold transition flex items-center gap-2 disabled:opacity-50"
            >
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              {loading ? 'Synthesizing...' : 'Run Ghostwriter Engine'}
            </button>
          </div>
        </div>

        {results ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-500">
            <div className="space-y-6">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 relative overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Linkedin className="w-5 h-5 text-blue-400" />
                    <h3 className="font-bold text-slate-200">LinkedIn Hook</h3>
                  </div>
                  <button 
                    onClick={() => handlePublish('li')}
                    disabled={publishStatus.li === 'publishing' || publishStatus.li === 'success'}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded transition ${publishStatus.li === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg'}`}
                  >
                    {publishStatus.li === 'success' ? 'Live on LinkedIn ✓' : publishStatus.li === 'publishing' ? 'Posting...' : <><Send className="w-3 h-3"/> One-Click Publish</>}
                  </button>
                </div>
                <div className="whitespace-pre-wrap text-slate-300 text-sm bg-slate-900 p-4 rounded-lg border border-slate-700">
                  {results.linkedin}
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Twitter className="w-5 h-5 text-slate-300" />
                    <h3 className="font-bold text-slate-200">X (Twitter) Thread</h3>
                  </div>
                  <button 
                    onClick={() => handlePublish('tw')}
                    disabled={publishStatus.tw === 'publishing' || publishStatus.tw === 'success'}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded transition ${publishStatus.tw === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 hover:bg-slate-600 text-white'}`}
                  >
                    {publishStatus.tw === 'success' ? 'Live on X ✓' : publishStatus.tw === 'publishing' ? 'Tweeting...' : <><Send className="w-3 h-3"/> Dispatch Thread</>}
                  </button>
                </div>
                <div className="space-y-3">
                  {results.twitter?.map((tweet, i) => (
                    <div key={i} className="text-slate-300 text-sm bg-slate-900 p-4 rounded-lg border border-slate-700 relative">
                      <span className="absolute top-2 right-2 text-[10px] bg-slate-800 px-1.5 rounded text-slate-500">{i+1}/{results.twitter?.length}</span>
                      {tweet}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <PenTool className="w-5 h-5 text-fuchsia-400" />
                  <h3 className="font-bold text-slate-200">Article Expansion</h3>
                </div>
                <button 
                    onClick={() => handlePublish('ar')}
                    disabled={publishStatus.ar === 'publishing' || publishStatus.ar === 'success'}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded transition ${publishStatus.ar === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-fuchsia-600 hover:bg-fuchsia-500 text-white shadow-lg'}`}
                  >
                    {publishStatus.ar === 'success' ? 'Live on CMS ✓' : publishStatus.ar === 'publishing' ? 'Pushing...' : <><Send className="w-3 h-3"/> Publish to Web</>}
                  </button>
              </div>
              <div 
                className="text-slate-300 text-sm bg-slate-900 p-6 rounded-lg prose prose-invert max-w-none border border-slate-700 h-[calc(100%-3rem)] overflow-auto"
                dangerouslySetInnerHTML={{ __html: results.article || '' }}
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 opacity-50">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <Linkedin className="w-6 h-6 text-blue-400 mb-4" />
              <h3 className="font-bold text-slate-200 mb-2">LinkedIn Formatting</h3>
              <p className="text-sm text-slate-400">Generates hook-first architecture. 1-click publishing via OAuth.</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <Twitter className="w-6 h-6 text-slate-300 mb-4" />
              <h3 className="font-bold text-slate-200 mb-2">X (Twitter) Threads</h3>
              <p className="text-sm text-slate-400">Pulls core concepts into serialized loop threads.</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <PenTool className="w-6 h-6 text-fuchsia-400 mb-4" />
              <h3 className="font-bold text-slate-200 mb-2">Long-form Articles</h3>
              <p className="text-sm text-slate-400">Expands verbal bullets into strategic Medium drafts.</p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
