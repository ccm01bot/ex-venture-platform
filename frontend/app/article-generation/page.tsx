'use client';

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import {
  FileText, Linkedin, Instagram, Facebook,
  Sparkles, Settings,
  Image as ImageIcon, Video, UploadCloud, Brush,
  Monitor, Clapperboard, Box, Image
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

  const [generating, setGenerating] = useState(false);
  const [article, setArticle] = useState<{ title: string; content: string; image: string } | null>(null);
  const [error, setError] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setError('');
    setArticle(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/articles/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            platform,
            tone,
            topic,
            keywords: '', // We can derive this if needed or add a field
            length: length.toLowerCase(),
            video_url: videoUrl,
            image_style: imageStyle
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
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">AI Image Generation</h2>
              <div className="bg-cyan-500/10 text-cyan-400 text-xs font-semibold px-2 py-1 rounded-full border border-cyan-500/20">Enabled</div>
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
                src={article.image}
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
            
            <div className="p-8">
              <div className="flex gap-3 mb-8 pb-8 border-b border-slate-800">
                <a
                  href={article.image}
                  download={`${article.title.replace(/\s+/g, '-').toLowerCase()}.svg`}
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
              </div>
              
              <div 
                className="prose prose-invert prose-lg max-w-none 
                prose-headings:text-white prose-a:text-cyan-400 
                prose-li:marker:text-cyan-500 prose-blockquote:border-l-cyan-500 
                prose-blockquote:bg-slate-800/50 prose-blockquote:rounded-r-lg prose-blockquote:py-2 prose-blockquote:px-6
                leading-relaxed text-slate-300"
                dangerouslySetInnerHTML={{ __html: article.content }}
              />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
