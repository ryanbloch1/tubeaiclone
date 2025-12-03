"use client";

import { useAuth } from '@/components/auth/AuthProvider';
import Link from 'next/link';
import { useEffect, useState, useCallback } from 'react';
import { useToastContext } from '@/components/providers/ToastProvider';
import { Trash2, Loader2 } from 'lucide-react';

type Project = {
  id: string;
  title: string;
  topic: string | null;
  status: 'draft' | 'script' | 'voiceover' | 'images' | 'complete';
  // Real estate fields
  video_type?: 'listing' | 'neighborhood_guide' | 'market_update';
  property_address?: string;
  property_type?: string;
  property_price?: number;
  bedrooms?: number;
  bathrooms?: number;
  created_at: string;
  updated_at: string;
};

type SortOption = 'recent' | 'title' | 'oldest';
type VideoTypeFilter = 'all' | 'listing' | 'neighborhood_guide' | 'market_update';

export default function ProjectsPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-emerald-50">
      <div className="container mx-auto px-4 py-10">
        <RecentProjects />
      </div>
    </main>
  );
}

function RecentProjects() {
  const { user } = useAuth();
  const toast = useToastContext();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('recent');
  const [videoTypeFilter, setVideoTypeFilter] = useState<VideoTypeFilter>('all');
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [pendingDeletes, setPendingDeletes] = useState<Map<string, NodeJS.Timeout>>(new Map());

  const fetchProjects = useCallback(async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/projects');
      if (!res.ok) {
        throw new Error('Failed to fetch projects');
      }
      const data = await res.json();
      setProjects(data.projects || data || []);
    } catch (e) {
      setError('Failed to load projects. Please try again.');
      console.error('Error fetching projects:', e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const sortProjects = useCallback((projects: Project[], sortBy: SortOption) => {
    const sorted = [...projects];
    switch (sortBy) {
      case 'recent':
        return sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      case 'title':
        return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
      case 'oldest':
        return sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      default:
        return sorted;
    }
  }, []);

  const handleDelete = useCallback((project: Project) => {
    // Optimistically remove from UI
    setProjects(prev => prev.filter(p => p.id !== project.id));
    setDeletingIds(prev => new Set(prev).add(project.id));

    // Show undo toast
    const toastId = toast.success(
      `Project "${project.title}" deleted`,
      {
        onUndo: () => {
          // Restore project
          setProjects(prev => [...prev, project].sort((a, b) => 
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
          ));
          setDeletingIds(prev => {
            const newSet = new Set(prev);
            newSet.delete(project.id);
            return newSet;
          });
          
          // Clear any pending delete timeout
          const timeout = pendingDeletes.get(project.id);
          if (timeout) {
            clearTimeout(timeout);
            setPendingDeletes(prev => {
              const newMap = new Map(prev);
              newMap.delete(project.id);
              return newMap;
            });
          }
        },
        undoLabel: 'Restore'
      }
    );

    // Set up actual delete after 5 seconds
    const timeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/projects/${project.id}`, {
          method: 'DELETE',
        });
        
        if (!res.ok) {
          throw new Error('Failed to delete project');
        }
        
        // Clean up state
        setDeletingIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(project.id);
          return newSet;
        });
        setPendingDeletes(prev => {
          const newMap = new Map(prev);
          newMap.delete(project.id);
          return newMap;
        });
      } catch (e) {
        // Restore project on error
        setProjects(prev => [...prev, project].sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        ));
        setDeletingIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(project.id);
          return newSet;
        });
        toast.error('Failed to delete project. Please try again.');
      }
    }, 5000);

    setPendingDeletes(prev => new Map(prev).set(project.id, timeout));
  }, [toast, pendingDeletes]);

  const getProjectRoute = (project: Project) => {
    if (!project.status || project.status === 'draft' || project.status === 'script') return `/script?projectId=${project.id}`;
    if (project.status === 'voiceover') return `/voiceover?projectId=${project.id}`;
    if (project.status === 'images') return `/images?projectId=${project.id}`;
    return `/script?projectId=${project.id}`;
  };

  const getStepBadge = (step: Project['status']) => {
    switch (step) {
      case 'draft':
        return { text: 'Draft', color: 'bg-gray-50 text-gray-700 border-gray-200' };
      case 'script':
        return { text: 'Script Ready', color: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 'voiceover':
        return { text: 'Voiceover Ready', color: 'bg-green-50 text-green-700 border-green-200' };
      case 'images':
        return { text: 'Images Ready', color: 'bg-purple-50 text-purple-700 border-purple-200' };
      case 'complete':
        return { text: 'Complete', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      default:
        return { text: 'Draft', color: 'bg-gray-50 text-gray-700 border-gray-200' };
    }
  };

  // Filter projects by video type
  const filteredProjects = videoTypeFilter === 'all' 
    ? projects 
    : projects.filter(p => p.video_type === videoTypeFilter);
  
  const sortedProjects = sortProjects(filteredProjects, sortBy);
  
  // Calculate stats
  const stats = {
    listings: projects.filter(p => p.video_type === 'listing').length,
    neighborhoodGuides: projects.filter(p => p.video_type === 'neighborhood_guide').length,
    marketUpdates: projects.filter(p => p.video_type === 'market_update').length,
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-slate-900">Your Projects</h1>
          <Link
            href="/script?new=1"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + New Project
          </Link>
        </div>
        
        {/* Stats */}
        <div className="flex flex-wrap gap-4 mb-4 text-sm">
          <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full">
            {stats.listings} Listing Videos
          </div>
          <div className="bg-green-50 text-green-700 px-3 py-1 rounded-full">
            {stats.neighborhoodGuides} Neighborhood Guides
          </div>
          <div className="bg-purple-50 text-purple-700 px-3 py-1 rounded-full">
            {stats.marketUpdates} Market Updates
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex items-center space-x-4">
          <select
            value={videoTypeFilter}
            onChange={(e) => setVideoTypeFilter(e.target.value as VideoTypeFilter)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Video Types</option>
            <option value="listing">Property Listings</option>
            <option value="neighborhood_guide">Neighborhood Guides</option>
            <option value="market_update">Market Updates</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="recent">Recently Updated</option>
            <option value="title">Title A-Z</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-xl p-6 animate-pulse">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="h-5 bg-slate-200 rounded mb-2"></div>
                  <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                </div>
                <div className="h-6 bg-slate-200 rounded-full w-20"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-1/2 mb-4"></div>
              <div className="h-10 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <h4 className="text-xl font-semibold text-slate-900 mb-2">Failed to load projects</h4>
          <p className="text-slate-600 mb-6">{error}</p>
          <button
            onClick={fetchProjects}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      ) : sortedProjects.length === 0 ? (
        <div className="text-center py-12">
          <h4 className="text-xl font-semibold text-slate-900 mb-2">No projects yet</h4>
          <p className="text-slate-600 mb-6">Create your first video project to get started</p>
          <Link
            href="/script?new=1"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Create Your First Project
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedProjects.map((project) => {
            const stepBadge = getStepBadge(project.status);
            const isDeleting = deletingIds.has(project.id);
            
            return (
              <div 
                key={project.id} 
                className={`bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg transition-all duration-200 ${
                  isDeleting ? 'opacity-50' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-slate-900 mb-1">{project.title || 'Untitled Project'}</h4>
                    {project.property_address && (
                      <p className="text-sm text-slate-700 font-medium mb-1">{project.property_address}</p>
                    )}
                    {project.property_type && (
                      <p className="text-xs text-slate-500 mb-1 capitalize">{project.property_type.replace('_', ' ')}</p>
                    )}
                    {(project.bedrooms || project.bathrooms || project.property_price) && (
                      <p className="text-xs text-slate-600 mb-2">
                        {project.bedrooms && project.bathrooms && `${project.bedrooms}BR/${project.bathrooms}BA`}
                        {project.property_price && ` • $${project.property_price.toLocaleString()}`}
                      </p>
                    )}
                    {!project.property_address && project.topic && (
                      <p className="text-sm text-slate-600 mb-2">Topic: {project.topic}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${stepBadge.color}`}>{stepBadge.text}</span>
                    <button
                      onClick={() => handleDelete(project)}
                      disabled={isDeleting}
                      className="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-50"
                      title="Delete project"
                    >
                      {isDeleting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="text-sm text-slate-500 mb-4">Updated {new Date(project.updated_at).toLocaleDateString()}</div>
                <Link 
                  href={getProjectRoute(project)} 
                  className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors text-center"
                >
                  Continue Project →
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

