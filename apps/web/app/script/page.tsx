"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { ContextModal } from "./ui/ContextModal";
import { StyleModal } from "./ui/StyleModal";

type ScriptResponse = { 
  script?: string; 
  scriptId?: string;
  projectId?: string;
  error?: string; 
  mock?: boolean 
};

const MODEL_OPTIONS = [
  { value: 'auto', label: 'Auto (best available)' },
  { value: 'groq:llama-3.1-8b-instant', label: 'Groq - Llama 3.1 8B Instant' },
  { value: 'groq:llama-3.3-70b-versatile', label: 'Groq - Llama 3.3 70B Versatile' },
  { value: 'gemini:gemini-1.5-flash', label: 'Google - Gemini 1.5 Flash' },
  { value: 'openai:gpt-4o-mini', label: 'OpenAI - GPT-4o Mini' },
  { value: 'anthropic:claude-3-5-haiku-latest', label: 'Anthropic - Claude 3.5 Haiku' },
];

const parseModelSelection = (selection: string): { modelProvider?: string; modelName?: string } => {
  if (selection === 'auto') {
    return {};
  }
  const [modelProvider, modelName] = selection.split(':', 2);
  if (!modelProvider || !modelName) {
    return {};
  }
  return { modelProvider, modelName };
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
  // Real estate fields
  property_type?: string;
  property_address?: string;
  property_price?: number;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  mls_number?: string;
  property_features?: string[];
  video_type?: 'listing' | 'neighborhood_guide' | 'market_update';
  created_at: string;
  updated_at: string;
};

type ProjectPhoto = {
  id: string;
  image_data_url: string | null;
  analysed: boolean;
  sort_index?: number | null;
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
  const [scriptModel, setScriptModel] = useState('auto');
  const [editableScript, setEditableScript] = useState('');
  
  // Real estate form state
  const [videoType, setVideoType] = useState<'listing' | 'neighborhood_guide' | 'market_update'>('listing');
  const [propertyAddress, setPropertyAddress] = useState('');
  const [propertyType, setPropertyType] = useState('');
  const [propertyPrice, setPropertyPrice] = useState<number | ''>('');
  const [bedrooms, setBedrooms] = useState<number | ''>('');
  const [bathrooms, setBathrooms] = useState<number | ''>('');
  const [squareFeet, setSquareFeet] = useState<number | ''>('');
  const [mlsNumber, setMlsNumber] = useState('');
  const [propertyFeatures, setPropertyFeatures] = useState<string[]>([]);
  const [showPropertyForm, setShowPropertyForm] = useState(true); // Show by default

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
  const [photoStatus, setPhotoStatus] = useState<{ uploaded: number; analysed: number; minRequired: number } | null>(null);
  const [uploadingPhotos, setUploadingPhotos] = useState(false);
  const [projectPhotos, setProjectPhotos] = useState<ProjectPhoto[]>([]);
  const [dragPhotoId, setDragPhotoId] = useState<string | null>(null);

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

  // Ensure we always have a default style selected (prefer real estate styles)
  useEffect(() => {
    if (!style) {
      setStyle('Professional Real Estate');
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
        setStyle(project.style || 'Professional Real Estate');
        setMode(project.mode || 'script');
        setTemperature(project.temperature || 0.7);
        setWordCount(project.word_count || 500);
        setSelection(project.selection || '');
        setExtraContext(project.extra_context || '');
        setImageCount(project.image_count || 10);
        setVideoLength(project.video_length || '1:00');
        
        // Populate real estate fields
        setVideoType(project.video_type || 'listing');
        setPropertyAddress(project.property_address || '');
        setPropertyType(project.property_type || '');
        setPropertyPrice(project.property_price || '');
        setBedrooms(project.bedrooms || '');
        setBathrooms(project.bathrooms || '');
        setSquareFeet(project.square_feet || '');
        setMlsNumber(project.mls_number || '');
        // Handle property_features - could be array or JSON string
        let features = project.property_features || [];
        if (typeof features === 'string') {
          try {
            features = JSON.parse(features);
          } catch {
            features = [];
          }
        }
        setPropertyFeatures(Array.isArray(features) ? features : []);
        setShowPropertyForm(!!(project.property_address || project.video_type));
        
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

  const refreshPhotoStatus = useCallback(async (pid: string) => {
    try {
      const resp = await fetch(`/api/project/photos-status?projectId=${encodeURIComponent(pid)}`, {
        cache: 'no-store',
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data && data.success) {
        setPhotoStatus({
          uploaded: data.uploaded_count ?? 0,
          analysed: data.analysed_count ?? 0,
          minRequired: data.min_required ?? 5,
        });
      }
    } catch (e) {
      console.error('Failed to load photo status', e);
    }
  }, []);

  const loadProjectPhotos = useCallback(async (pid: string) => {
    try {
      const resp = await fetch(`/api/project-photos/list?projectId=${encodeURIComponent(pid)}`, {
        cache: 'no-store',
      });
      if (!resp.ok) {
        console.error('Failed to load photos:', resp.status, await resp.text());
        return;
      }
      const data = await resp.json();
      if (data && data.success && Array.isArray(data.photos)) {
        const mapped = data.photos.map((p: ProjectPhoto) => ({
          id: p.id,
          image_data_url: p.image_data_url ?? null,
          analysed: !!p.analysed,
          sort_index: p.sort_index ?? null,
        }));
        setProjectPhotos(mapped);
      } else {
        console.warn('[LOAD_PHOTOS] Invalid response format:', data);
      }
    } catch (e) {
      console.error('Failed to load project photos', e);
    }
  }, []);

  // Refresh photo status when projectId changes
  useEffect(() => {
    if (projectId) {
      refreshPhotoStatus(projectId);
      loadProjectPhotos(projectId);
    }
  }, [projectId, refreshPhotoStatus, loadProjectPhotos]);

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
    
    // Auto-save project if we don't have a projectId yet
    let currentProjectId = projectId;
    if (!currentProjectId) {
      try {
        const resp = await fetch('/api/projects/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            projectId: null,
            topic: topic || propertyAddress || 'Property Listing',
            style,
            mode,
            temperature,
            wordCount,
            imageCount,
            videoLength,
            selection,
            extraContext,
            videoType,
            propertyAddress,
            propertyType: propertyType || 'other',
            propertyPrice: propertyPrice || undefined,
            bedrooms: bedrooms || undefined,
            bathrooms: bathrooms || undefined,
            squareFeet: squareFeet || undefined,
            mlsNumber: mlsNumber || undefined,
            propertyFeatures,
          }),
        });
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(data.error || `Failed to save project (${resp.status})`);
        }
        if (data.projectId) {
          currentProjectId = data.projectId;
          setProjectId(data.projectId);
        }
      } catch (e) {
        console.error('Failed to save project', e);
        setError(e instanceof Error ? e.message : 'Failed to save project');
        setLoading(false);
        return;
      }
    }
    
    try {
      const { modelProvider, modelName } = parseModelSelection(scriptModel);
      const response = await fetch("/api/script/generate", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({
          topic: topic || propertyAddress || 'Property Listing', // Use property address as topic if no custom title
          style: style || 'Professional Real Estate',
          mode,
          temperature,
          wordCount,
          selection: mode === "script" ? undefined : selection || undefined,
          extraContext: extraContext || undefined,
          imageCount,
          videoLength,
          projectId: currentProjectId,
          // Real estate fields
          videoType,
          propertyAddress,
          propertyType: propertyType || 'other',
          propertyPrice: propertyPrice || undefined,
          bedrooms: bedrooms || undefined,
          bathrooms: bathrooms || undefined,
          squareFeet: squareFeet || undefined,
          mlsNumber: mlsNumber || undefined,
          propertyFeatures,
          modelProvider,
          modelName,
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

  // Helper to ensure we have a project ID (creates one if needed)
  const ensureProjectId = async (): Promise<string | null> => {
    if (projectId) return projectId;
    
    // Need to create project - but only if we have minimum required info
    if (!propertyAddress && !topic.trim()) {
      setError('Please enter a property address or title before uploading photos');
      return null;
    }
    
    try {
      const resp = await fetch('/api/projects/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectId: null,
          topic: topic || propertyAddress || 'Property Listing',
          style,
          mode,
          temperature,
          wordCount,
          imageCount,
          videoLength,
          selection,
          extraContext,
          videoType,
          propertyAddress,
          propertyType: propertyType || 'other',
          propertyPrice: propertyPrice || undefined,
          bedrooms: bedrooms || undefined,
          bathrooms: bathrooms || undefined,
          squareFeet: squareFeet || undefined,
          mlsNumber: mlsNumber || undefined,
          propertyFeatures,
        }),
      });
      
      if (!resp.ok) {
        const text = await resp.text();
        let errorMsg = 'Failed to create project';
        try {
          const data = JSON.parse(text);
          errorMsg = data.error || data.detail || errorMsg;
        } catch {
          errorMsg = text || errorMsg;
        }
        throw new Error(errorMsg);
      }
      
      const data = await resp.json();
      if (data.projectId) {
        setProjectId(data.projectId);
        return data.projectId;
      } else {
        throw new Error('No project ID returned');
      }
    } catch (e) {
      console.error('Failed to create project', e);
      setError(e instanceof Error ? e.message : 'Failed to create project');
      return null;
    }
  };

  const handleUploadPhotos = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    // Ensure we have a project ID (creates one if needed)
    const currentProjectId = await ensureProjectId();
    if (!currentProjectId) {
      // Error already set by ensureProjectId
      return;
    }
    
    setUploadingPhotos(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        const reader = new FileReader();
        const loadPromise = new Promise<void>((resolve, reject) => {
          reader.onloadend = async () => {
            try {
              const base64Data = (reader.result as string).split(',')[1] || '';
              const resp = await fetch('/api/project-photos/upload', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  project_id: currentProjectId,
                  image_data: base64Data,
                  image_filename: file.name,
                }),
              });
              if (!resp.ok) {
                const text = await resp.text();
                let errorMsg = `Upload failed (${resp.status})`;
                try {
                  const data = JSON.parse(text);
                  errorMsg = data.error || data.detail || errorMsg;
                } catch {
                  errorMsg = text || errorMsg;
                }
                throw new Error(errorMsg);
              }
              resolve();
            } catch (e) {
              reject(e);
            }
          };
          reader.onerror = () => reject(new Error('Failed to read file'));
        });
        reader.readAsDataURL(file);
        await loadPromise;
      }
      // Refresh both status and photos after all uploads complete
      await Promise.all([
        refreshPhotoStatus(currentProjectId),
        loadProjectPhotos(currentProjectId),
      ]);
    } catch (e) {
      console.error('Failed to upload photos', e);
      setError(e instanceof Error ? e.message : 'Failed to upload photos');
    } finally {
      setUploadingPhotos(false);
    }
  };

  const handlePhotoDragStart = (id: string) => {
    setDragPhotoId(id);
  };

  const handlePhotoDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handlePhotoDrop = async (targetId: string) => {
    if (!dragPhotoId || dragPhotoId === targetId || !projectId) return;
    const current = [...projectPhotos];
    const fromIndex = current.findIndex((p) => p.id === dragPhotoId);
    const toIndex = current.findIndex((p) => p.id === targetId);
    if (fromIndex === -1 || toIndex === -1) return;
    const [moved] = current.splice(fromIndex, 1);
    current.splice(toIndex, 0, moved);
    setProjectPhotos(current);

    try {
      await fetch('/api/project-photos/reorder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          image_ids: current.map((p) => p.id),
        }),
      });
    } catch (e) {
      console.error('Failed to persist photo order', e);
    } finally {
      setDragPhotoId(null);
    }
  };

  const goToVoiceover = () => {
    if (projectId) {
      router.push(`/voiceover?projectId=${projectId}`);
    } else {
      router.push("/voiceover");
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Create Property Listing Video</h1>
            <p className="text-slate-600">Enter property details and we&apos;ll generate a professional script automatically</p>
          </div>
          
          <form onSubmit={onSubmit} className="space-y-6">
            {/* Main Property Form - Always Visible */}
            <div className="bg-white border-2 border-blue-200 rounded-xl shadow-lg p-8 space-y-6">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-1 h-8 bg-blue-600 rounded-full"></div>
                <h2 className="text-2xl font-bold text-slate-900">Property Information</h2>
            </div>

              {/* Video Type - Prominent */}
              <div>
                <label htmlFor="video-type" className="block text-sm font-semibold text-slate-700 mb-2">
                  Video Type <span className="text-red-500">*</span>
                </label>
                <select
                  id="video-type"
                  value={videoType}
                  onChange={(e) => setVideoType(e.target.value as typeof videoType)}
                  className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 font-medium"
                  required
                >
                  <option value="listing">Property Listing</option>
                  <option value="neighborhood_guide">Neighborhood Guide</option>
                  <option value="market_update">Market Update</option>
                </select>
              </div>
              
              {/* Property Address - Primary Input */}
              <div>
                <label htmlFor="property-address" className="block text-sm font-semibold text-slate-700 mb-2">
                  Property Address
                </label>
                <input
                  type="text"
                  id="property-address"
                  value={propertyAddress}
                  onChange={(e) => {
                    setPropertyAddress(e.target.value);
                    // Auto-set topic if empty
                    if (!topic.trim()) {
                      setTopic(e.target.value);
                    }
                  }}
                  placeholder="123 Main Road, Suburb, City"
                  className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200 placeholder-slate-400"
                />
                <p className="text-xs text-slate-500 mt-1">This will be used as the video title if no custom title is provided</p>
              </div>
              
              {/* Property Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-200">
                  
                <div>
                  <label htmlFor="property-type" className="block text-sm font-semibold text-slate-700 mb-2">
                    Property Type
                  </label>
                  <select
                    id="property-type"
                    value={propertyType}
                    onChange={(e) => setPropertyType(e.target.value)}
                    className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  >
                    <option value="">Select type</option>
                    <option value="house">House</option>
                    <option value="apartment">Apartment / Flat</option>
                    <option value="townhouse">Townhouse</option>
                    <option value="cluster">Cluster</option>
                    <option value="farm">Farm</option>
                    <option value="vacant_land">Vacant Land / Plot</option>
                    <option value="commercial">Commercial Property</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label htmlFor="property-price" className="block text-sm font-semibold text-slate-700 mb-2">
                    Price (Rands)
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-medium">R</span>
                    <input
                      type="number"
                      id="property-price"
                      value={propertyPrice}
                      onChange={(e) => setPropertyPrice(e.target.value ? parseFloat(e.target.value) : '')}
                      placeholder="450,000"
                      min="0"
                      step="1000"
                      className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 pl-8 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor="bedrooms" className="block text-sm font-semibold text-slate-700 mb-2">
                    Bedrooms
                  </label>
                  <input
                    type="number"
                    id="bedrooms"
                    value={bedrooms}
                    onChange={(e) => setBedrooms(e.target.value ? parseInt(e.target.value) : '')}
                    placeholder="3"
                    min="0"
                    className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                
                <div>
                  <label htmlFor="bathrooms" className="block text-sm font-semibold text-slate-700 mb-2">
                    Bathrooms
                  </label>
                  <input
                    type="number"
                    id="bathrooms"
                    value={bathrooms}
                    onChange={(e) => setBathrooms(e.target.value ? parseFloat(e.target.value) : '')}
                    placeholder="2.5"
                    min="0"
                    step="0.5"
                    className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                
                <div>
                  <label htmlFor="square-feet" className="block text-sm font-semibold text-slate-700 mb-2">
                    Floor Area (m²)
                  </label>
                  <input
                    type="number"
                    id="square-feet"
                    value={squareFeet}
                    onChange={(e) => setSquareFeet(e.target.value ? parseInt(e.target.value) : '')}
                    placeholder="1,800"
                    min="0"
                    className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                
                <div>
                  <label htmlFor="mls-number" className="block text-sm font-semibold text-slate-700 mb-2">
                    MLS Number <span className="text-slate-400 font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    id="mls-number"
                    value={mlsNumber}
                    onChange={(e) => setMlsNumber(e.target.value)}
                    placeholder="MLS123456"
                    className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                </div>
              </div>
              
              {/* Property Features */}
              <div className="pt-4 border-t border-slate-200">
                <label className="block text-sm font-semibold text-slate-700 mb-3">
                  Property Features
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    'swimming_pool',
                    'garden',
                    'double_garage',
                    'covered_parking',
                    'pet_friendly',
                    'security_estate',
                    'security_complex',
                    '24hr_security',
                    'alarm_system',
                    'electric_fence',
                    'solar_power',
                    'backup_power',
                    'borehole',
                    'irrigation_system',
                    'staff_quarters',
                    'flatlet',
                    'balcony',
                    'patio',
                    'built_in_braai',
                    'air_conditioning',
                    'sea_view',
                    'mountain_view',
                  ].map((feature) => (
                    <label
                      key={feature}
                      className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={propertyFeatures.includes(feature)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPropertyFeatures([...propertyFeatures, feature]);
                          } else {
                            setPropertyFeatures(propertyFeatures.filter((f) => f !== feature));
                          }
                        }}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                      />
                      <span className="text-sm text-slate-700 capitalize font-medium">
                        {feature.replace(/_/g, ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Video Settings - Collapsible */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
              <button
                type="button"
                onClick={() => setShowPropertyForm(!showPropertyForm)}
                className="flex items-center justify-between w-full text-left"
              >
                <h3 className="text-lg font-semibold text-slate-900">Video Settings</h3>
                <span className="text-slate-500">{showPropertyForm ? '▼' : '▶'}</span>
              </button>
              
              {showPropertyForm && (
                <div className="mt-4 space-y-4 pt-4 border-t border-slate-200">
                  {/* Custom Title (Optional) */}
                  <div>
                    <label htmlFor="custom-title" className="block text-sm font-semibold text-slate-700 mb-2">
                      Custom Video Title <span className="text-slate-400 font-normal">(optional)</span>
                    </label>
                    <input
                      type="text"
                      id="custom-title"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder={propertyAddress || "Enter a custom title, or leave blank to use property address"}
                      className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                    />
                    <p className="text-xs text-slate-500 mt-1">If left blank, the property address will be used as the title</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="video-length" className="block text-sm font-semibold text-slate-700 mb-2">
                      Video Length
                    </label>
                      <select
                        id="video-length"
                        value={videoLength}
                        onChange={(e) => setVideoLength(e.target.value)}
                        className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      >
                        <option value="0:30">0:30 (Short)</option>
                        <option value="1:00">1:00 (Standard)</option>
                        <option value="2:00">2:00 (Extended)</option>
                        <option value="3:00">3:00 (Long)</option>
                      </select>
                    </div>
                    
                    <div>
                      <label htmlFor="script-model" className="block text-sm font-semibold text-slate-700 mb-2">
                        Script Model
                      </label>
                      <select
                        id="script-model"
                        value={scriptModel}
                        onChange={(e) => setScriptModel(e.target.value)}
                        className="w-full rounded-lg border-2 border-slate-300 px-4 py-3 text-base bg-white text-black focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      >
                        {MODEL_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Upload Photos section - images-first flow */}
            {(propertyAddress || topic.trim()) && (
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Property Photos</h3>
                  <p className="text-sm text-slate-600">
                    Upload photos of your property. We&apos;ll automatically save your listing and use these photos to write a script that matches your images.
                  </p>
                </div>
                <div className="mt-2 space-y-3">
                  <label className="block">
                    <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl py-6 px-4 cursor-pointer hover:border-slate-400 transition-colors bg-slate-50">
                      <div className="text-2xl mb-2">Upload</div>
                      <div className="text-sm font-medium text-slate-900">
                        {uploadingPhotos ? 'Uploading photos…' : 'Click or drag images here to upload'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        JPG or PNG. Upload at least 5 photos (exterior, living room, kitchen, bedrooms, bathroom).
                      </div>
                    </div>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={(e) => handleUploadPhotos(e.target.files)}
                      disabled={uploadingPhotos}
                    />
                  </label>
                  {photoStatus && (
                    <div className="text-xs text-slate-600">
                      <span className="font-semibold">{photoStatus.uploaded}</span> photos uploaded,&nbsp;
                      <span className="font-semibold">{photoStatus.analysed}</span> analysed.{" "}
                      {photoStatus.analysed < photoStatus.minRequired ? (
                        <span>
                          Need at least <span className="font-semibold">{photoStatus.minRequired}</span> analysed photos to enable script generation.
                        </span>
                      ) : (
                        <span className="text-green-700 font-semibold">You&apos;re ready to generate a photo-grounded script.</span>
                      )}
                    </div>
                  )}
                  {projectPhotos.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-slate-600 mb-2">
                        Drag to arrange the order your photos will appear in the video and script.
                      </p>
                      <div className="flex flex-wrap gap-3">
                        {projectPhotos.map((photo) => (
                          <div
                            key={photo.id}
                            className={`w-28 h-20 rounded-md overflow-hidden border ${
                              dragPhotoId === photo.id ? 'border-blue-500' : 'border-slate-300'
                            } bg-slate-100 flex items-center justify-center relative cursor-move`}
                            draggable
                            onDragStart={() => handlePhotoDragStart(photo.id)}
                            onDragOver={handlePhotoDragOver}
                            onDrop={() => handlePhotoDrop(photo.id)}
                          >
                            {photo.image_data_url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img
                                src={photo.image_data_url}
                                alt="Property photo"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <span className="text-xs text-slate-500">No preview</span>
                            )}
                            <span
                              className={`absolute bottom-1 left-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${
                                photo.analysed
                                  ? 'bg-green-600 text-white'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}
                            >
                              {photo.analysed ? 'Analysed' : 'Analysing…'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Generate Button - Prominent */}
            <div className="bg-gradient-to-r from-blue-600 to-green-600 rounded-xl shadow-lg p-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="text-white">
                  <h3 className="text-xl font-bold mb-1">Ready to Generate Script</h3>
                  <p className="text-blue-100 text-sm">
                    {propertyAddress 
                      ? `We'll create a professional script for ${propertyAddress}`
                      : 'Enter property details above to generate your script'}
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={
                    loading ||
                    (!propertyAddress && !topic.trim()) ||
                    // If any photos uploaded, require min analysed before enabling
                    (photoStatus
                      ? photoStatus.uploaded > 0 && photoStatus.analysed < photoStatus.minRequired
                      : false)
                  }
                  className="bg-white text-blue-600 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed px-8 py-4 rounded-lg font-bold text-lg transition-all transform hover:scale-105 shadow-lg whitespace-nowrap"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin">⏳</span>
                      Generating Script...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      Generate Professional Script
                    </span>
                  )}
                </button>
              </div>
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
          <div className="max-w-5xl mx-auto mt-8 space-y-6">
            {result.mock && (
              <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4">
                <p className="text-amber-800 text-sm font-medium">Mock fallback (no API key detected)</p>
              </div>
            )}
            
            {/* Property Summary Card - Enhanced */}
            {(propertyAddress || propertyType || propertyPrice || bedrooms || bathrooms) && (
              <div className="bg-gradient-to-r from-blue-50 via-green-50 to-blue-50 rounded-xl border-2 border-blue-300 p-6 shadow-md">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">Property</span>
                  <h3 className="text-lg font-bold text-slate-900">Property Summary</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {propertyAddress && (
                    <div className="bg-white/80 rounded-lg p-3">
                      <span className="text-xs text-slate-600 font-medium block mb-1">Address</span>
                      <p className="font-semibold text-slate-900 text-sm">{propertyAddress}</p>
                    </div>
                  )}
                  {propertyType && (
                    <div className="bg-white/80 rounded-lg p-3">
                      <span className="text-xs text-slate-600 font-medium block mb-1">Type</span>
                      <p className="font-semibold text-slate-900 text-sm capitalize">{propertyType.replace('_', ' ')}</p>
                    </div>
                  )}
                  {(bedrooms || bathrooms) && (
                    <div className="bg-white/80 rounded-lg p-3">
                      <span className="text-xs text-slate-600 font-medium block mb-1">Size</span>
                      <p className="font-semibold text-slate-900 text-sm">
                        {bedrooms && bathrooms ? `${bedrooms}BR/${bathrooms}BA` : bedrooms ? `${bedrooms}BR` : `${bathrooms}BA`}
                      </p>
                    </div>
                  )}
                  {propertyPrice && (
                    <div className="bg-white/80 rounded-lg p-3">
                      <span className="text-xs text-slate-600 font-medium block mb-1">Price</span>
                      <p className="font-semibold text-slate-900 text-sm">R{propertyPrice.toLocaleString()}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Script Editor - Enhanced */}
            <div className="bg-white rounded-xl border-2 border-slate-300 shadow-lg p-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <label className="block text-lg font-bold text-slate-900 mb-1">
                    Generated Script
              </label>
                  <p className="text-sm text-slate-600">Review and edit the AI-generated script below</p>
                </div>
                <button
                  type="button"
                  onClick={saveScript}
                  disabled={saving || !result?.scriptId}
                  data-save-button
                  className="bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                >
                  {saving ? 'Saving...' : '💾 Save Changes'}
                </button>
              </div>
              <textarea
                className="w-full rounded-lg border-2 border-slate-300 p-6 text-slate-900 bg-slate-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-none font-mono text-sm leading-relaxed"
                rows={20}
                value={editableScript}
                onChange={(e) => setEditableScript(e.target.value)}
                placeholder="Your generated script will appear here..."
              />
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={goToVoiceover}
                  className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white px-8 py-4 rounded-lg font-bold text-lg transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-xl flex items-center gap-2"
                >
                  <span>Continue to Voiceover</span>
                  <span>→</span>
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
