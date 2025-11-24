"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { TitleBar } from "./ui/TitleBar";
import { ContextModal } from "./ui/ContextModal";
import { StyleModal } from "./ui/StyleModal";

const STYLE_PRESETS = [
  { value: 'Photorealistic', label: 'Photorealistic Cinematic' },
  { value: 'Comic Book', label: 'Comic Book Illustration' },
  { value: 'Studio Ghibli', label: 'Studio Ghibli Animation' },
  { value: 'Cyberpunk Neon', label: 'Cyberpunk Neon' },
  { value: 'Watercolor Storybook', label: 'Watercolor Storybook' },
];

type ScriptResponse = { 
  script?: string; 
  scriptId?: string;
  projectId?: string;
  error?: string; 
  mock?: boolean 
};

type Project = {
  id: string;
  title: string;
  topic: string;
  style: string;
  mode: string;
  temperature: number;
  word_count: number;
  image_count: number;
  video_length: string;
  selection: string;
  extra_context: string;
  created_at: string;
  updated_at: string;
};

export default function ScriptPage() {
  return (
    <AuthGuard>
      <ScriptPageContent />
    </AuthGuard>
  );
}

function ScriptPageContent() {
  const router = useRouter();
  const { session } = useAuth();
  
  // Form state
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('');
  const [mode, setMode] = useState<'script' | 'outline' | 'rewrite'>('script');
  const [temperature, setTemperature] = useState(0.7);
  const [wordCount, setWordCount] = useState(500);
  const [selection, setSelection] = useState('');
  const [extraContext, setExtraContext] = useState('');
  const [imageCount, setImageCount] = useState(10);
  const [videoLength, setVideoLength] = useState('1:00');
  const [editableScript, setEditableScript] = useState('');

  // Projects state
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [projects, setProjects] = useState<Project[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // UI state
  const [showContextModal, setShowContextModal] = useState(false);
  const [showStyleModal, setShowStyleModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScriptResponse | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  // Load projects
  const loadProjects = useCallback(async () => {
    try {
      const response = await fetch('/api/projects', {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  }, [session?.access_token]);

  // Load projects on mount
  useEffect(() => {
    if (session) {
      loadProjects();
    }
  }, [session, loadProjects]);

  // Ensure we always have a default style selected
  useEffect(() => {
    if (!style) {
      setStyle(STYLE_PRESETS[0]?.value || 'Photorealistic');
    }
  }, [style]);

  // Load a specific project
  const loadProject = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/projects/${id}`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        const project = data.project;
        const script = data.script;
        
        // Populate form fields
        setTopic(project.topic || '');
        setStyle(project.style || STYLE_PRESETS[0]?.value || 'Photorealistic');
        setMode(project.mode || 'script');
        setTemperature(project.temperature || 0.7);
        setWordCount(project.word_count || 500);
        setSelection(project.selection || '');
        setExtraContext(project.extra_context || '');
        setImageCount(project.image_count || 10);
        setVideoLength(project.video_length || '1:00');
        
        // Load script if exists
        if (script) {
          setEditableScript(script.edited_script || script.raw_script || '');
          setResult({
            script: script.edited_script || script.raw_script,
            scriptId: script.id,
            projectId: project.id
          });
          setProjectId(project.id);
        }
        
        setSelectedProject(project);
      }
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  }, [session?.access_token]);

  // Load project from URL parameters
  useEffect(() => {
    if (session && typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const projectIdParam = urlParams.get('projectId');
      if (projectIdParam && projectIdParam !== projectId) {
        setProjectId(projectIdParam);
        loadProject(projectIdParam);
      }
    }
  }, [session, projectId, loadProject]);

  // Save script edits
  const saveScript = async () => {
    if (!result?.scriptId || !editableScript) return;
    
    setSaving(true);
    try {
      const response = await fetch('/api/script/update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({
          scriptId: result.scriptId,
          content: editableScript
        })
      });
      
      if (response.ok) {
        // Show success feedback
        const saveButton = document.querySelector('[data-save-button]') as HTMLButtonElement;
        if (saveButton) {
          const originalText = saveButton.textContent;
          saveButton.textContent = 'Saved!';
          saveButton.classList.add('bg-green-600');
          setTimeout(() => {
            saveButton.textContent = originalText;
            saveButton.classList.remove('bg-green-600');
          }, 2000);
        }
      } else {
        throw new Error('Failed to save script');
      }
    } catch (error) {
      console.error('Failed to save script:', error);
      setError('Failed to save script changes');
    } finally {
      setSaving(false);
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    
    try {
      const response = await fetch("/api/script/generate", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({
          topic,
          style: style || STYLE_PRESETS[0]?.value,
          mode,
          temperature,
          wordCount,
          selection: mode === "script" ? undefined : selection || undefined,
          extraContext: extraContext || undefined,
          imageCount,
          videoLength,
          projectId
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      
      setResult(data);
      setProjectId(data.projectId);
      setEditableScript(data.script || "");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Update image count when video length changes
  useEffect(() => {
    const lengthToImages: { [key: string]: number } = {
      "0:30": 5,
      "1:00": 10,
      "2:00": 20,
      "3:00": 30
    };
    const next = lengthToImages[videoLength] || 10;
    if (next !== imageCount) {
      setImageCount(next);
    }
  }, [videoLength, imageCount]);

  const goToVoiceover = () => {
    if (projectId) {
      router.push(`/voiceover?projectId=${projectId}`);
    } else {
      router.push("/voiceover");
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900 mb-8 text-center">Script Generation</h1>
          
          <form onSubmit={onSubmit} className="space-y-4">
            <TitleBar
              topic={topic}
              setTopic={setTopic}
              videoLength={videoLength}
              onVideoLengthChange={setVideoLength}
              onOpenContextModal={() => setShowContextModal(true)}
              onOpenStyleModal={() => setShowStyleModal(true)}
              loading={loading}
              canSubmit={!!topic.trim()}
            />
            <div className="text-sm text-slate-500 pl-4">
              Credits remaining: 0  |  Estimated script credits: 0
            </div>

            <div className="mt-6 bg-white border border-slate-200 rounded-lg shadow-sm p-6 space-y-4">
              <div>
                <label htmlFor="visual-style" className="block text-sm font-medium text-slate-700 mb-2">
                  Visual Style
                </label>
                <p className="text-xs text-slate-500 mb-3">
                  Choose a consistent visual style to apply across your script and generated images.
                </p>
                <select
                  id="visual-style"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
                >
                  {STYLE_PRESETS.map((preset) => (
                    <option key={preset.value} value={preset.value}>
                      {preset.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                onClick={() => setShowStyleModal(true)}
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Customize or add a new style →
              </button>
            </div>
          </form>
        </div>

        {error && (
          <div className="max-w-4xl mx-auto mt-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {result?.script && (
          <div className="max-w-4xl mx-auto mt-8 space-y-6">
            {result.mock && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-amber-700 text-sm">Mock fallback (no API key detected)</p>
              </div>
            )}
            
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Edit script
              </label>
              <textarea
                className="w-full rounded-lg border border-black p-4 text-black bg-white focus:border-black focus:ring-2 focus:ring-black focus:ring-opacity-20 transition-colors resize-none"
                rows={15}
                value={editableScript}
                onChange={(e) => setEditableScript(e.target.value)}
                placeholder="Your generated script will appear here..."
              />
              
              <div className="mt-6 flex justify-between">
                <button
                  type="button"
                  onClick={saveScript}
                  disabled={saving || !result?.scriptId}
                  data-save-button
                  className="bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={goToVoiceover}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg"
                >
                  Use for Voiceover →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modals */}
        <ContextModal
          open={showContextModal}
          value={extraContext}
          onClose={() => setShowContextModal(false)}
          onSave={(txt: string) => { setExtraContext(txt); setShowContextModal(false); }}
        />
        <StyleModal
          open={showStyleModal}
          onClose={() => setShowStyleModal(false)}
          onCreate={(name: string) => { setStyle(name); setShowStyleModal(false); }}
        />
      </div>
    </main>
  );
}