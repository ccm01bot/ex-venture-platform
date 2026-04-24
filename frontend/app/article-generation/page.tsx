'use client';

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import {
  FileText, Linkedin, Instagram, Facebook,
  Sparkles, Settings,
  Image as ImageIcon, Video, UploadCloud, Brush,
  Monitor, Clapperboard, Box, Image,
  Globe, Link2, Plus, X, Search, ExternalLink, Send
} from 'lucide-react';

const PLATFORMS = [
  { id: 'Article', icon: <FileText className="w-5 h-5 mb-2" />, label: 'Article', desc: 'SEO-optimized blog post' },
  { id: 'LinkedIn', icon: <Linkedin className="w-5 h-5 mb-2" />, label: 'LinkedIn', desc: 'Professional networking' },
  { id: 'Instagram', icon: <Instagram className="w-5 h-5 mb-2" />, label: 'Instagram', desc: 'Visual storytelling' },
  { id: 'Facebook', icon: <Facebook className="w-5 h-5 mb-2" />, label: 'Facebook', desc: 'Community engagement' }
];

const TONES = [
  { id: 'Professional', emoji: '💼', label: 'Professional' },
  { id: 'Casual', emoji: '😊', label: 'Casual' },
  { id: 'Inspirational', emoji: '🚀', label: 'Inspirational' },
  { id: 'Technical', emoji: '⚙️', label: 'Technical' },
  { id: 'Storytelling', emoji: '📖', label: 'Storytelling' }
];

const LENGTHS = [
  { id: 'Short', words: '~300', label: 'Short', desc: 'Quick overview' },
  { id: 'Medium', words: '~500', label: 'Medium', desc: 'Standard post' },
  { id: 'Long', words: '~800', label: 'Long', desc: 'Detailed article' },
  { id: 'In-Depth', words: '~1,200', label: 'In-Depth', desc: 'Comprehensive' },
  { id: 'Deep Dive', words: '~2,000', label: 'Deep Dive', desc: 'Feature article' }
];

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

export default function ArticleGenerationPage() {
  const [platform, setPlatform] = useState('Article');
  const [tone, setTone] = useState('Professional');
  const [topic, setTopic] = useState('');
  const [length, setLength] = useState('Long');
  const [videoUrl, setVideoUrl] = useState('');
  const [imageStyle, setImageStyle] = useState('Photorealistic');
  const [webResearch, setWebResearch] = useState(false);
  const [sourceUrls, setSourceUrls] = useState<string[]>([]);
  const [newUrl, setNewUrl] = useState('');

  const [generating, setGenerating] = useState(false);
  const [article, setArticle] = useState<{ title: string; content: string; images: string[]; sources?: Array<{url: string; title: string}> } | null>(null);
  const [selectedImageIdx, setSelectedImageIdx] = useState(0);
  const [imageQuality, setImageQuality] = useState('draft');
  const [generatingMore, setGeneratingMore] = useState(false);
  const [error, setError] = useState('');

  // CMS Publishing States
  const [companies, setCompanies] = useState<{id: string, name: string, cms_platform: string}[]>([]);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState('');
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    // Fetch companies for the CMS publishing dropdown
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/companies`)
      .then(res => res.json())
      .then(data => setCompanies(data))
      .catch(console.error);
  }, []);

  const handlePublish = async () => {
    if (!article || !selectedCompanyId) return;
    setPublishing(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/publish/${selectedCompanyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: article.title,
          content_html: article.content,
          hero_image_url: article.images[selectedImageIdx] || ""
        }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to publish to CMS');
      
      alert(`Success! Article successfully published via ${data.provider}.`);
      setPublishModalOpen(false);
    } catch (err: any) {
      console.error(err);
      alert(`Error publishing: ${err.message}`);
    } finally {
      setPublishing(false);
    }
  };

  const handleGenerateAnother = async () => {
    if (!article) return;
    setGeneratingMore(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/articles/hero-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: article.title,
          image_style: imageStyle,
          image_quality: imageQuality
        }),
      });

      if (!response.ok) throw new Error('Failed to generate extra image');
      const data = await response.json();
      
      setArticle(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          images: [...prev.images, data.url]
        };
      });
      setSelectedImageIdx(article.images.length); 
    } catch (err) {
      console.error(err);
      alert('Failed to generate another variation.');
    } finally {
      setGeneratingMore(false);
    }
  };

  const addSourceUrl = () => {
    if (newUrl.trim() && sourceUrls.length < 5) {
      setSourceUrls([...sourceUrls, newUrl.trim()]);
      setNewUrl('');
    }
  };
  const removeSourceUrl = (i: number) => setSourceUrls(sourceUrls.filter((_, idx) => idx !== i));

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setError('');
    setArticle(null);
    setSelectedImageIdx(0);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/articles/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            platform,
            tone,
            topic,
            keywords: '',
            length: length.toLowerCase(),
            video_url: videoUrl,
            image_style: imageStyle,
            image_quality: imageQuality,
            web_research: webResearch,
            source_urls: sourceUrls.length > 0 ? sourceUrls : undefined
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate content');
      }

      const data = await response.json();
      setArticle(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-10 pb-20">
        <div>
          <h1 className="text-4xl font-extrabold text-white mb-2">Create Content</h1>
          <p className="text-slate-400">Generate hyper-optimized articles, social posts, and dynamic images using advanced AI pipelines.</p>
        </div>

        <form onSubmit={handleGenerate} className="space-y-10">
          
          {/* Platform Section */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">Choose Platform</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setPlatform(p.id)}
                  className={`p-4 rounded-xl border text-left transition ${
                    platform === p.id 
                      ? 'bg-cyan-600/10 border-cyan-500 text-cyan-400' 
                      : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800'
                  }`}
                >
                  {p.icon}
                  <div className="font-semibold text-white">{p.label}</div>
                  <div className="text-xs opacity-75 mt-1">{p.desc}</div>
                </button>
              ))}
            </div>
          </section>

          {/* Tone & Topic Section */}
          <section className="space-y-6">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">Tone & Topic</h2>
            
            <div className="flex flex-wrap gap-3">
              {TONES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTone(t.id)}
                  className={`px-4 py-2 rounded-full border transition flex items-center gap-2 ${
                    tone === t.id
                      ? 'bg-slate-700 border-slate-500 text-white'
                      : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span>{t.emoji}</span>
                  <span className="font-medium text-sm">{t.label}</span>
                </button>
              ))}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Topic <span className="text-slate-500 font-normal">(optional — AI will choose the best angle if left empty)</span>
              </label>
              <textarea
                rows={3}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition resize-none"
                placeholder='e.g., "How Bali Internship is transforming the industry..."'
              />
            </div>
          </section>

          {/* Web Research Section */}
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Globe className="w-5 h-5 text-cyan-400" />
              Web Research
              <span className="text-xs font-normal text-slate-500 ml-2">Feed real data into your article</span>
            </h2>

            {/* Auto-research toggle */}
            <button
              type="button"
              onClick={() => setWebResearch(!webResearch)}
              className={`flex items-center gap-3 w-full p-4 rounded-xl border transition ${
                webResearch
                  ? 'bg-cyan-600/10 border-cyan-500 text-cyan-300'
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
              }`}
            >
              <Search className="w-5 h-5" />
              <div className="text-left flex-1">
                <div className="font-semibold text-sm">Auto Web Research</div>
                <div className="text-xs opacity-70">AI will search the web for your topic, scrape top results, and use real data in the article</div>
              </div>
              <div className={`w-10 h-6 rounded-full relative transition ${webResearch ? 'bg-cyan-500' : 'bg-slate-600'}`}>
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${webResearch ? 'translate-x-5' : 'translate-x-1'}`} />
              </div>
            </button>

            {/* Manual source URLs */}
            <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 space-y-3">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
                <Link2 className="w-4 h-4 text-purple-400" />
                Reference URLs <span className="text-slate-500 font-normal">(optional — paste articles to use as sources)</span>
              </label>

              <div className="flex gap-2">
                <input
                  type="url"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSourceUrl())}
                  placeholder="https://example.com/article-to-reference"
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition"
                />
                <button
                  type="button"
                  onClick={addSourceUrl}
                  disabled={!newUrl.trim() || sourceUrls.length >= 5}
                  className="px-3 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 rounded-lg text-white text-sm transition flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" /> Add
                </button>
              </div>

              {sourceUrls.length > 0 && (
                <div className="space-y-2">
                  {sourceUrls.map((url, i) => (
                    <div key={i} className="flex items-center gap-2 bg-slate-900/60 rounded-lg px-3 py-2 text-xs">
                      <ExternalLink className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                      <span className="text-slate-300 truncate flex-1">{url}</span>
                      <button type="button" onClick={() => removeSourceUrl(i)} className="text-slate-500 hover:text-red-400 transition">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                  <p className="text-[10px] text-slate-600">{sourceUrls.length}/5 sources added</p>
                </div>
              )}
            </div>
          </section>

          {/* Advanced Options */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-slate-400" />
              <h2 className="text-xl font-bold text-slate-100">Advanced options</h2>
            </div>
            
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-300">Article Length</label>
              <p className="text-xs text-slate-500">Choose how long you want the article to be. Longer articles provide more depth, detail, and SEO value.</p>
              
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                {LENGTHS.map((l) => (
                  <button
                    key={l.id}
                    type="button"
                    onClick={() => setLength(l.id)}
                    className={`p-3 rounded-lg border text-center transition ${
                      length === l.id
                        ? 'bg-cyan-600/10 border-cyan-500 text-cyan-400'
                        : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800'
                    }`}
                  >
                    <div className="text-sm font-bold text-slate-100">{l.words}</div>
                    <div className="font-semibold text-white my-1">{l.label}</div>
                    <div className="text-[10px] opacity-75">{l.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-slate-800">
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Video className="w-4 h-4" /> Video Inspiration <span className="text-slate-500 font-normal">(optional)</span>
                </label>
                <p className="text-xs text-slate-500">Paste a YouTube, Vimeo, or any video link. The AI will extract the transcript and base the article on the actual spoken content.</p>
                <input
                  type="text"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="https://www.youtube.com/watch?v=..."
                />
              </div>

              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Image className="w-4 h-4" /> Your Photos <span className="text-slate-500 font-normal">(optional)</span>
                </label>
                <p className="text-xs text-slate-500">Upload your own photos to embed directly in the article. The AI will place them at relevant points in the text.</p>
                <div className="w-full bg-slate-900 border border-slate-700 border-dashed rounded-lg px-4 py-3 flex items-center justify-center text-slate-500 cursor-pointer hover:bg-slate-800 transition hover:text-slate-300">
                  <UploadCloud className="w-5 h-5 mr-2" /> Upload Photos
                </div>
              </div>
            </div>
          </section>

          {/* Image Generation Styles */}
          <section className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">AI Image Generation</h2>
              <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
                <button
                  type="button"
                  onClick={() => setImageQuality('draft')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${imageQuality === 'draft' ? 'bg-emerald-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                >
                  Draft (Free)
                </button>
                <button
                  type="button"
                  onClick={() => setImageQuality('premium')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${imageQuality === 'premium' ? 'bg-fuchsia-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                >
                  Premium ($0.03)
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-500 mb-2">Choose the visual style for your generated image:</p>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {STYLES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setImageStyle(s.id)}
                  className={`p-3 flex flex-col items-center justify-center text-center rounded-lg border transition ${
                    imageStyle === s.id
                      ? 'bg-fuchsia-600/10 border-fuchsia-500 text-fuchsia-400'
                      : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                  }`}
                >
                  <div className="mb-2">{s.icon}</div>
                  <div className="font-semibold text-white text-xs mb-1">{s.label}</div>
                  <div className="text-[10px] opacity-75">{s.desc}</div>
                </button>
              ))}
            </div>
          </section>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-center gap-3">
              <div className="bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center font-bold text-xs">!</div>
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <div className="pt-6 border-t border-slate-800">
            <button
              type="submit"
              disabled={generating}
              className="w-full md:w-auto bg-gradient-to-r from-cyan-600 to-cyan-600 hover:from-cyan-500 hover:to-cyan-500 disabled:opacity-50 text-white font-bold px-8 py-4 rounded-xl shadow-lg shadow-cyan-500/20 transition transform hover:-translate-y-1"
            >
              {generating ? '✨ Generating AI Content...' : 'Generate Stunning Content'}
            </button>
          </div>
        </form>

        {article && (
          <div className="max-w-4xl mt-12 bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl">
            <div className="relative h-96 w-full bg-slate-800">
              <img
                src={article.images[selectedImageIdx]}
                alt={article.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent opacity-90" />
              <div className="absolute bottom-0 left-0 p-8 w-full">
                <span className="inline-block bg-cyan-600 font-bold px-3 py-1 rounded-full text-xs text-white uppercase tracking-wider mb-3">
                  {platform} • {tone}
                </span>
                <h2 className="text-3xl md:text-5xl font-extrabold text-white leading-tight filter drop-shadow-lg">{article.title}</h2>
              </div>
            </div>

            {article.images && article.images.length > 0 && (
              <div className="flex bg-slate-950 border-b border-t border-slate-700 overflow-x-auto overflow-y-hidden items-center">
                <div className="flex gap-4 p-5 shrink-0">
                  <span className="text-slate-400 text-sm font-semibold flex items-center shrink-0 mr-2">Hero Image Options:</span>
                  {article.images.map((img, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setSelectedImageIdx(idx)}
                      className={`h-20 w-36 shrink-0 rounded-xl overflow-hidden border-2 transition ${selectedImageIdx === idx ? 'border-cyan-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'border-slate-700 opacity-60 hover:opacity-100 hover:border-slate-500'}`}
                    >
                      <img src={img} className="w-full h-full object-cover" alt={`Option ${idx+1}`} />
                    </button>
                  ))}
                </div>

                <div className="px-5 shrink-0 border-l border-slate-800 flex items-center h-full">
                  <button
                    type="button"
                    disabled={generatingMore}
                    onClick={handleGenerateAnother}
                    className="h-12 px-4 rounded-xl border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800 transition flex items-center gap-2 text-sm font-semibold disabled:opacity-50"
                  >
                    {generatingMore ? 'Generating...' : '+ Generate Another'}
                  </button>
                </div>
              </div>
            )}
            
            <div className="p-8">
              <div className="flex gap-3 mb-8 pb-8 border-b border-slate-800">
                <a
                  href={article.images[selectedImageIdx]}
                  download={`${article.title.replace(/\s+/g, '-').toLowerCase()}.png`}
                  className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition"
                >
                  Download Asset
                </a>
                <button
                  onClick={() => navigator.clipboard.writeText(`# ${article.title}\n\n${article.content}`)}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition shadow-lg shadow-cyan-500/20"
                >
                  Copy Format
                </button>
                <button
                  onClick={() => setPublishModalOpen(true)}
                  className="bg-fuchsia-600 hover:bg-fuchsia-500 text-white text-sm font-bold px-6 py-2.5 rounded-lg transition shadow-lg shadow-fuchsia-500/20 flex items-center gap-2 ml-auto"
                >
                  <Send className="w-4 h-4" /> Publish to Website
                </button>
              </div>
              
              <div 
                className="prose prose-invert prose-lg max-w-none 
                prose-headings:text-white prose-a:text-cyan-400 
                prose-li:marker:text-cyan-500 prose-blockquote:border-l-cyan-500 
                prose-blockquote:bg-slate-800/50 prose-blockquote:rounded-r-lg prose-blockquote:py-2 prose-blockquote:px-6
                leading-relaxed text-slate-300"
                dangerouslySetInnerHTML={{ __html: article.content }}
              />

              {article.sources && article.sources.length > 0 && (
                <div className="mt-8 pt-6 border-t border-slate-800">
                  <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-cyan-400" />
                    Web Sources Used ({article.sources.length})
                  </h3>
                  <div className="space-y-2">
                    {article.sources.map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-xs text-slate-400 hover:text-cyan-400 transition group"
                      >
                        <ExternalLink className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-500" />
                        <span className="truncate">{src.title}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {publishModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Send className="w-5 h-5 text-fuchsia-400" />
                Publish Article
              </h3>
              <button disabled={publishing} onClick={() => setPublishModalOpen(false)} className="text-slate-500 hover:text-white disabled:opacity-50">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <p className="text-sm text-slate-400">
                Instantly distribute this generated article directly to a configured company CMS (WordPress or Webhook).
              </p>
              
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Select Company Website</label>
                <select 
                  value={selectedCompanyId}
                  onChange={(e) => setSelectedCompanyId(e.target.value)}
                  disabled={publishing}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-fuchsia-500 focus:ring-1 focus:ring-fuchsia-500"
                >
                  <option value="" disabled>-- Select target company --</option>
                  {companies.filter(c => c.cms_platform && c.cms_platform !== 'none').map(c => (
                    <option key={c.id} value={c.id}>{c.name} ({c.cms_platform.toUpperCase()})</option>
                  ))}
                </select>
                {companies.filter(c => c.cms_platform && c.cms_platform !== 'none').length === 0 && (
                  <p className="text-xs text-red-400 mt-2">
                    No companies have CMS details configured yet. Configure this in the Companies dashboard first.
                  </p>
                )}
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800 mt-6">
                <button
                  onClick={handlePublish}
                  disabled={publishing || !selectedCompanyId}
                  className="bg-fuchsia-600 hover:bg-fuchsia-500 disabled:opacity-50 text-white font-bold px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 transition w-full justify-center"
                >
                  {publishing ? 'Publishing...' : 'Confirm & Publish'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
