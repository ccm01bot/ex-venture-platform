'use client';

import { useState } from 'react';
import { Sparkles, Download, Image as ImageIcon, Wand2, Palette, Maximize, ZoomIn, Copy, Check, Loader2 } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STYLE_PRESETS = [
  { id: 'photorealistic', name: 'Photorealistic', icon: '📸', desc: 'Ultra-real 8K photography' },
  { id: 'digital_art', name: 'Digital Art', icon: '🎨', desc: 'Vibrant illustrations' },
  { id: '3d_render', name: '3D Render', icon: '🧊', desc: 'Octane render quality' },
  { id: 'cinematic', name: 'Cinematic', icon: '🎬', desc: 'Movie scene aesthetic' },
  { id: 'watercolor', name: 'Watercolor', icon: '🖌️', desc: 'Soft artistic painting' },
  { id: 'minimalist', name: 'Minimalist', icon: '◻️', desc: 'Clean flat design' },
  { id: 'anime', name: 'Anime', icon: '⛩️', desc: 'Studio Ghibli style' },
  { id: 'logo', name: 'Logo Design', icon: '✏️', desc: 'Professional branding' },
  { id: 'thumbnail', name: 'YT Thumbnail', icon: '▶️', desc: 'Hormozi/GaryVee style' },
  { id: 'hero_image', name: 'Hero Image', icon: '🖥️', desc: 'Tech editorial photo' },
];

const SIZES = [
  { id: '1024x1024', label: 'Square', desc: '1:1' },
  { id: '1792x1024', label: 'Landscape', desc: '16:9' },
  { id: '1024x1792', label: 'Portrait', desc: '9:16' },
];

const QUALITIES = [
  { id: 'standard', label: 'Standard', desc: 'Fast generation' },
  { id: 'hd', label: 'HD', desc: 'Higher detail' },
];

export default function ImageGeneratorPage() {
  const [prompt, setPrompt] = useState('');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [size, setSize] = useState('1024x1024');
  const [quality, setQuality] = useState('standard');
  const [style, setStyle] = useState<'vivid' | 'natural'>('vivid');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ url: string; revised_prompt: string; error?: string } | null>(null);
  const [history, setHistory] = useState<Array<{ url: string; prompt: string; timestamp: string }>>([]);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim() && !selectedPreset) return;
    setLoading(true);
    setResult(null);

    const finalPrompt = selectedPreset
      ? `${selectedPreset} ${prompt}`.trim()
      : prompt;

    try {
      const res = await fetch(`${API}/api/images/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: finalPrompt, size, quality, style }),
      });
      const data = await res.json();
      setResult(data);
      if (data.url && !data.error) {
        setHistory(prev => [
          { url: data.url, prompt: finalPrompt, timestamp: new Date().toLocaleTimeString() },
          ...prev.slice(0, 11),
        ]);
      }
    } catch {
      setResult({ url: '', revised_prompt: '', error: 'Failed to connect to backend.' });
    } finally {
      setLoading(false);
    }
  };

  const copyPrompt = () => {
    if (result?.revised_prompt) {
      navigator.clipboard.writeText(result.revised_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-fuchsia-500 to-purple-600 mb-4">
          <Wand2 className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-fuchsia-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          AI Image Generator
        </h1>
        <p className="text-gray-400 mt-2">Create stunning visuals with DALL·E 3 — powered by OpenAI</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Controls */}
        <div className="lg:col-span-1 space-y-6">
          {/* Prompt */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm">
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-3">
              <Sparkles className="w-4 h-4 text-fuchsia-400" />
              Describe Your Image
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A futuristic city at sunset with flying cars and neon signs..."
              className="w-full bg-gray-900/60 border border-gray-600/40 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 resize-none h-32 text-sm"
            />
          </div>

          {/* Style Presets */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm">
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-3">
              <Palette className="w-4 h-4 text-purple-400" />
              Style Preset
            </label>
            <div className="grid grid-cols-2 gap-2">
              {STYLE_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => setSelectedPreset(selectedPreset === preset.id ? null : preset.id)}
                  className={`text-left p-2.5 rounded-xl border transition-all text-xs ${
                    selectedPreset === preset.id
                      ? 'border-fuchsia-500 bg-fuchsia-500/10 text-fuchsia-300'
                      : 'border-gray-700/50 bg-gray-900/40 text-gray-400 hover:border-gray-600 hover:text-gray-300'
                  }`}
                >
                  <span className="text-base">{preset.icon}</span>
                  <div className="font-medium mt-0.5">{preset.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Size & Quality */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm space-y-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                <Maximize className="w-4 h-4 text-cyan-400" />
                Size
              </label>
              <div className="flex gap-2">
                {SIZES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSize(s.id)}
                    className={`flex-1 py-2 px-3 rounded-lg border text-xs font-medium transition-all ${
                      size === s.id
                        ? 'border-cyan-500 bg-cyan-500/10 text-cyan-300'
                        : 'border-gray-700/50 text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {s.label}
                    <span className="block text-[10px] opacity-60">{s.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-300 mb-2 block">Quality</label>
              <div className="flex gap-2">
                {QUALITIES.map((q) => (
                  <button
                    key={q.id}
                    onClick={() => setQuality(q.id)}
                    className={`flex-1 py-2 px-3 rounded-lg border text-xs font-medium transition-all ${
                      quality === q.id
                        ? 'border-purple-500 bg-purple-500/10 text-purple-300'
                        : 'border-gray-700/50 text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {q.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-300 mb-2 block">Mood</label>
              <div className="flex gap-2">
                {(['vivid', 'natural'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setStyle(s)}
                    className={`flex-1 py-2 px-3 rounded-lg border text-xs font-medium capitalize transition-all ${
                      style === s
                        ? 'border-fuchsia-500 bg-fuchsia-500/10 text-fuchsia-300'
                        : 'border-gray-700/50 text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={loading || (!prompt.trim() && !selectedPreset)}
            className="w-full py-4 rounded-xl font-bold text-white bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-sm shadow-lg shadow-fuchsia-500/20"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Wand2 className="w-5 h-5" />
                Generate Image
              </>
            )}
          </button>
        </div>

        {/* Right: Result + History */}
        <div className="lg:col-span-2 space-y-6">
          {/* Result */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 backdrop-blur-sm min-h-[400px] flex items-center justify-center">
            {loading ? (
              <div className="text-center">
                <div className="relative w-20 h-20 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full border-4 border-gray-700"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-fuchsia-500 border-t-transparent animate-spin"></div>
                  <Wand2 className="absolute inset-0 m-auto w-8 h-8 text-fuchsia-400" />
                </div>
                <p className="text-gray-400 text-sm">DALL·E 3 is creating your image...</p>
                <p className="text-gray-600 text-xs mt-1">This typically takes 10-20 seconds</p>
              </div>
            ) : result ? (
              <div className="w-full space-y-4">
                {result.error && (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-amber-300 text-xs">
                    ⚠️ {result.error}
                  </div>
                )}
                {result.url && (
                  <div className="relative group">
                    <img
                      src={result.url}
                      alt="Generated image"
                      className="w-full rounded-xl shadow-2xl shadow-black/40"
                    />
                    <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 bg-black/70 rounded-lg text-white hover:bg-black/90 transition-colors backdrop-blur-sm"
                        title="Open full size"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </a>
                      <a
                        href={result.url}
                        download="generated-image.png"
                        className="p-2 bg-black/70 rounded-lg text-white hover:bg-black/90 transition-colors backdrop-blur-sm"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                )}
                {result.revised_prompt && (
                  <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-700/40">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-500 font-medium">DALL·E Revised Prompt</span>
                      <button onClick={copyPrompt} className="text-gray-500 hover:text-gray-300 transition-colors">
                        {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed">{result.revised_prompt}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center">
                <ImageIcon className="w-16 h-16 text-gray-700 mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Your generated image will appear here</p>
                <p className="text-gray-700 text-xs mt-1">Pick a style, describe what you want, hit generate</p>
              </div>
            )}
          </div>

          {/* History */}
          {history.length > 0 && (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Generation History</h3>
              <div className="grid grid-cols-4 gap-3">
                {history.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => setResult({ url: item.url, revised_prompt: item.prompt })}
                    className="relative group rounded-xl overflow-hidden border border-gray-700/40 hover:border-fuchsia-500/50 transition-all aspect-square"
                  >
                    <img src={item.url} alt="" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                      <span className="text-[10px] text-gray-300 line-clamp-2">{item.prompt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
