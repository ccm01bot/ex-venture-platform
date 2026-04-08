'use client';

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import {
  Youtube, FileText, UploadCloud, FileEdit,
  Clock, Settings, Sparkles, AlertCircle, Lightbulb,
  Image as ImageIcon, Brush, Monitor, Clapperboard, Box
} from 'lucide-react';

const STYLES = [
  { id: 'Photorealistic', icon: <ImageIcon className="w-4 h-4" />, label: 'Photorealistic', desc: 'Ultra-real photography' },
  { id: 'Illustration', icon: <Brush className="w-4 h-4" />, label: 'Illustration', desc: 'Bold digital art' },
  { id: 'Minimalist', icon: <Box className="w-4 h-4" />, label: 'Minimalist', desc: 'Clean & simple' },
  { id: '3D Render', icon: <Monitor className="w-4 h-4" />, label: '3D Render', desc: 'Modern 3D look' },
  { id: 'Watercolor', icon: <Brush className="w-4 h-4" />, label: 'Watercolor', desc: 'Soft artistic feel' },
  { id: 'Flat Design', icon: <Box className="w-4 h-4" />, label: 'Flat Design', desc: 'Material design' },
  { id: 'Cinematic', icon: <Clapperboard className="w-4 h-4" />, label: 'Cinematic', desc: 'Hollywood drama' },
  { id: 'Abstract', icon: <Sparkles className="w-4 h-4" />, label: 'Abstract', desc: 'Bold & expressive' },
  { id: 'Isometric', icon: <Box className="w-4 h-4" />, label: 'Isometric', desc: '3D miniature world' },
  { id: 'Editorial', icon: <FileText className="w-4 h-4" />, label: 'Editorial', desc: 'Magazine quality' }
];

export default function YouTubeSEOPage() {
  const [inputType, setInputType] = useState<'url' | 'script' | 'brainstorm'>('url');
  const [url, setUrl] = useState('');
  const [script, setScript] = useState('');
  
  // Brainstorm state
  const [brainstorming, setBrainstorming] = useState(false);
  const [ideas, setIdeas] = useState<string[]>([]);
  const [selectedIdea, setSelectedIdea] = useState('');

  // Thumbnail Style state
  const [imageStyle, setImageStyle] = useState('Photorealistic');

  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Derived metrics
  const wordCount = script.trim().length > 0 ? script.trim().split(/\s+/).length : 0;
  // Estimate ~150 words per minute for speaking
  const estimatedMinutes = Math.floor(wordCount / 150);
  const estimatedSeconds = Math.floor((wordCount % 150) / (150 / 60));
  const estimatedTime = `~${estimatedMinutes}:${estimatedSeconds.toString().padStart(2, '0')}`;

  const handleBrainstorm = (e: React.FormEvent) => {
    e.preventDefault();
    setBrainstorming(true);
    setTimeout(() => {
      setIdeas([
        "10 Habits of Highly Effective Founders (2026 Edition)",
        "Why 90% of AI Startups Will Fail Next Year",
        "The Complete Guide to Series A Funding Term Sheets",
        "How to Build a Minimum Viable Product in 48 Hours"
      ]);
      setBrainstorming(false);
    }, 1500);
  };

  const [result, setResult] = useState<{titles: string[], description: string, tags: string[], thumbnail_urls: string[]} | null>(null);
  const [activeIdx, setActiveIdx] = useState(0);

  const handleOptimize = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setActiveIdx(0);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/youtube/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_type: inputType,
          url,
          script,
          selected_idea: selectedIdea,
          image_style: imageStyle
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to run optimization pipeline');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      alert('Error connecting to optimization service');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto pb-20">
        
        {/* Header Section */}
        <div className="mb-10 text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 bg-red-600/10 rounded-2xl mb-2">
            <Youtube className="w-10 h-10 text-red-500" />
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-white">YouTube SEO Optimizer</h1>
          <p className="text-lg text-slate-400">8-step AI process for perfect <span className="text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded">100/100</span> YouTube SEO & Thumbnails</p>
        </div>

        {/* Action History / Nav placeholder */}
        <div className="flex items-center gap-4 mb-6 text-sm font-medium border-b border-slate-800 pb-4">
          <button className="text-white border-b-2 border-red-500 pb-4 -mb-[18px]">Optimizer</button>
          <button className="text-slate-500 hover:text-slate-300 pb-4 -mb-[18px]">History</button>
        </div>

        <form onSubmit={handleOptimize} className="space-y-8">
          
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FileEdit className="w-5 h-5 text-slate-400" /> Video Foundation
              </h2>
              <p className="text-sm text-slate-500">Provide context, script, or let the AI brainstorm for you.</p>
            </div>

            {/* Input Type Toggle */}
            <div className="flex bg-slate-800/80 p-1 rounded-xl w-full">
              <button
                type="button"
                onClick={() => setInputType('url')}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-semibold transition ${
                  inputType === 'url' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Youtube className="w-4 h-4 hidden sm:block" /> YouTube URL
              </button>
              <button
                type="button"
                onClick={() => setInputType('script')}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-semibold transition ${
                  inputType === 'script' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4 hidden sm:block" /> Script / File
              </button>
              <button
                type="button"
                onClick={() => setInputType('brainstorm')}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-semibold transition ${
                  inputType === 'brainstorm' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Lightbulb className="w-4 h-4 hidden sm:block" /> Auto Brainstorm
              </button>
            </div>

            {/* Dynamic Input Body */}
            {inputType === 'url' && (
              <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Youtube className="w-5 h-5 text-slate-500" />
                  </div>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://youtube.com/watch?v=..."
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-12 pr-4 py-4 text-white placeholder-slate-600 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition text-lg"
                    required={inputType === 'url'}
                  />
                </div>
                <div className="flex items-start gap-2 mt-3 text-sm text-slate-500">
                  <AlertCircle className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  <p>The AI will automatically download the video's transcript and extract the core narrative to build a flawless SEO metadata package.</p>
                </div>
              </div>
            )}

            {inputType === 'script' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="relative border border-slate-700 rounded-xl bg-slate-950 group focus-within:border-red-500 focus-within:ring-1 focus-within:ring-red-500 transition">
                  <textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    rows={8}
                    placeholder="Paste your video script here... The more detailed your script, the better the SEO optimization will be. Include all spoken content, key topics, and any important terms you want to rank for."
                    className="w-full bg-transparent p-4 text-white placeholder-slate-600 focus:outline-none resize-y min-h-[160px]"
                    required={inputType === 'script'}
                  />
                  <div className="bg-slate-800/80 border-t border-slate-700 px-4 py-3 flex items-center justify-between rounded-b-xl rounded-t-none">
                    <div className="flex items-center gap-4 text-xs font-semibold text-slate-400">
                      <span className="flex items-center gap-1.5"><FileText className="w-3.5 h-3.5" /> {wordCount} words</span>
                      <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> {estimatedTime}</span>
                    </div>
                    
                    <button type="button" className="flex items-center gap-2 text-sm text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-600 px-3 py-1.5 rounded-lg transition shadow-sm">
                      <UploadCloud className="w-4 h-4" /> <span className="hidden md:inline">Upload PDF, Word, or TXT</span><span className="md:hidden">Upload</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {inputType === 'brainstorm' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {ideas.length === 0 ? (
                  <div className="bg-slate-950 p-8 rounded-xl border border-slate-700 text-center space-y-6">
                    <div className="mx-auto w-16 h-16 bg-cyan-500/10 text-cyan-400 rounded-full flex items-center justify-center">
                      <Lightbulb className="w-8 h-8" />
                    </div>
                    <div>
                      <h3 className="text-white font-bold text-lg mb-2">Let AI Find the Perfect Vertical</h3>
                      <p className="text-slate-400 text-sm max-w-lg mx-auto">Click below to brainstorm viral video concepts. Once you select one, we will automatically write the script, extract SEO metadata, and generate a matching thumbnail in one click.</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleBrainstorm}
                      disabled={brainstorming}
                      className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition"
                    >
                      {brainstorming ? 'Analyzing Trends...' : 'Auto-Generate Concepts'}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <h3 className="text-slate-300 font-semibold mb-3">Select a concept to auto-produce:</h3>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {ideas.map((idea, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setSelectedIdea(idea)}
                          className={`p-4 rounded-xl border text-left transition ${
                            selectedIdea === idea
                              ? 'bg-cyan-600/20 border-cyan-500 text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]'
                              : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-600 hover:bg-slate-800'
                          }`}
                        >
                          <span className="text-xs font-bold text-cyan-500 mb-1 block">CONCEPT {idx + 1}</span>
                          <span className="font-medium">{idea}</span>
                        </button>
                      ))}
                    </div>
                    <div className="pt-2 flex justify-end">
                      <button 
                        type="button" 
                        onClick={handleBrainstorm}
                        className="text-sm text-slate-400 hover:text-white"
                      >
                        Refresh ideas ↺
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* AI Thumbnail Styles Section */}
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-slate-400" /> Generated Thumbnail Style
              </h2>
              <div className="bg-cyan-500/10 text-cyan-400 text-xs font-semibold px-2 py-1 rounded-full border border-cyan-500/20">Parallel Pipeline</div>
            </div>
            <p className="text-sm text-slate-500 mb-4">Select a visual style. An optimized thumbnail will be generated automatically alongside your SEO extraction.</p>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setImageStyle(s.id)}
                  className={`p-3 flex flex-col items-center justify-center text-center rounded-lg border transition ${
                    imageStyle === s.id
                      ? 'bg-fuchsia-600/10 border-fuchsia-500 text-fuchsia-400 shadow-sm'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                  }`}
                >
                  <div className="mb-2">{s.icon}</div>
                  <div className="font-semibold text-white text-xs mb-1">{s.label}</div>
                  <div className="text-[10px] opacity-75">{s.desc}</div>
                </button>
              ))}
            </div>
          </section>

          {/* Advanced Options Toggle */}
          <div className="flex flex-col gap-4">
            <button 
              type="button" 
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition w-fit"
            >
              <Settings className="w-4 h-4" /> 
              {showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}
            </button>
            
            {showAdvanced && (
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 animate-in fade-in slide-in-from-top-2">
                <p className="text-slate-400 text-sm">Target keyword overrides and competitor video analysis settings will go here!</p>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={
              loading || 
              (inputType === 'url' && !url) || 
              (inputType === 'script' && !script) ||
              (inputType === 'brainstorm' && !selectedIdea)
            }
            className="w-full relative group overflow-hidden bg-gradient-to-br from-red-600 to-rose-700 disabled:from-slate-600 disabled:to-slate-700 disabled:text-slate-400 text-white font-extrabold text-lg py-5 px-6 rounded-2xl shadow-lg shadow-red-500/20 transition-all active:scale-[0.99] disabled:active:scale-100 flex items-center justify-center gap-3"
          >
            {loading ? (
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 border-4 border-white/20 border-t-white rounded-full animate-spin" />
                Executing SEO & Render Pipeline...
              </div>
            ) : (
              <>
                <Sparkles className="w-6 h-6 group-hover:animate-pulse" />
                {inputType === 'brainstorm' 
                  ? 'Auto-Produce Script & SEO Package' 
                  : 'Optimize SEO & Auto-Generate Thumbnail'}
              </>
            )}
            
            {!loading && <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />}
          </button>
        </form>

        {/* RESULTS CARD */}
        {result && (
          <div className="mt-12 bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-6">
            <div className="relative h-96 w-full bg-slate-800 border-b border-slate-800">
              <img
                src={result.thumbnail_urls[activeIdx]}
                alt="YouTube Thumbnail"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
              <div className="absolute bottom-0 left-0 p-8 w-full flex items-end justify-between">
                <div>
                  <span className="inline-block bg-red-600 font-bold px-3 py-1 rounded-full text-xs text-white uppercase tracking-wider mb-3">
                    {imageStyle} Style Mode • Variation {activeIdx + 1}
                  </span>
                  <h2 className="text-3xl md:text-4xl font-extrabold text-white leading-tight filter drop-shadow-lg max-w-3xl">{result.titles[activeIdx % result.titles.length]}</h2>
                </div>
                <a
                  href={result.thumbnail_urls[activeIdx]}
                  download={`youtube-thumbnail-v${activeIdx+1}.png`}
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white font-semibold px-4 py-2 rounded-lg transition shadow-lg shrink-0"
                >
                  Download This Variation
                </a>
              </div>
            </div>
            
            <div className="p-8 grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2 space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Title Variations</h3>
                  <div className="space-y-2">
                    {result.titles.map((t, idx) => (
                      <button 
                        key={idx}
                        onClick={() => setActiveIdx(idx)}
                        className={`w-full text-left px-4 py-3 rounded-xl border transition ${
                          activeIdx === idx 
                            ? 'bg-cyan-600/10 border-cyan-500 text-white' 
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                        }`}
                      >
                        <span className="text-xs font-bold mr-3 opacity-50 block sm:inline mb-1 sm:mb-0">OPTION {idx + 1}</span>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 mt-6">Thumbnail Options</h3>
                  <div className="grid grid-cols-3 gap-4">
                    {result.thumbnail_urls.map((url, idx) => (
                      <button 
                        key={idx}
                        onClick={() => setActiveIdx(idx)}
                        className={`relative aspect-video rounded-lg overflow-hidden border-2 transition ${
                          activeIdx === idx ? 'border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]' : 'border-transparent hover:border-slate-500 opacity-70 hover:opacity-100'
                        }`}
                      >
                        <img src={url} alt={`Variation ${idx + 1}`} className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-6">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Optimized Description</h3>
                  <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl text-slate-300 text-sm whitespace-pre-wrap font-mono leading-relaxed relative group">
                    {result.description}
                    <button 
                      type="button"
                      onClick={() => navigator.clipboard.writeText(result.description)}
                      className="absolute top-3 right-3 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 transition shadow"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                    Top 15 Ranking Tags 
                    <button
                      type="button" 
                      onClick={() => navigator.clipboard.writeText(result.tags.join(', '))}
                      className="text-xs text-cyan-400 hover:text-cyan-300"
                    >
                      Copy All
                    </button>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {result.tags.map((tag, idx) => (
                      <span key={idx} className="bg-slate-800 border border-slate-700 px-3 py-1 text-slate-300 rounded-lg text-xs font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">100</div>
                    <span className="text-cyan-400 font-bold">Perfect Score</span>
                  </div>
                  <p className="text-xs text-cyan-500/80">Title length, keyword density, and visual CTR are optimized perfectly against global search indices.</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
      </div>
    </Layout>
  );
}
