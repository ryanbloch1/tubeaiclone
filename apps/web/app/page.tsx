"use client";

import { useAuth } from '@/components/auth/AuthProvider';
import Link from 'next/link';

export default function Home() {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold text-slate-900 mb-6">
              TubeAI Video Creator
            </h1>
            <p className="text-xl text-slate-600 mb-12">
              Create engaging YouTube videos with AI-powered scripts, voiceovers, and visuals
            </p>
            
            <div className="bg-white border border-slate-200 rounded-xl p-8 max-w-md mx-auto">
              <h2 className="text-2xl font-semibold text-slate-900 mb-4">Get Started</h2>
              <p className="text-slate-600 mb-6">
                Sign in to start creating amazing videos with AI
              </p>
              <div className="space-y-4">
                <Link 
                  href="/login"
                  className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Sign In
                </Link>
                <Link 
                  href="/signup"
                  className="block w-full bg-slate-100 hover:bg-slate-200 text-slate-700 px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Create Account
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Navigation Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900">TubeAI Video Creator</h1>
            <div className="flex items-center space-x-4">
              <span className="text-slate-600">Welcome, {user.email}</span>
              <button
                onClick={() => signOut()}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-slate-900 mb-6">
            Create Your Next Video
          </h2>
          <p className="text-xl text-slate-600 mb-12">
            Choose where to start in your video creation journey
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Link 
              href="/script" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-blue-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">1. Script Generation</h3>
              <p className="text-slate-600 text-sm">
                Generate compelling video scripts from your topic ideas
              </p>
              <div className="mt-4 text-blue-600 group-hover:text-blue-700 font-medium">
                Start Here →
              </div>
            </Link>
            
            <Link 
              href="/voiceover" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-purple-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">🎙️</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">2. Voice Generation</h3>
              <p className="text-slate-600 text-sm">
                Add professional AI voices to your existing scripts
              </p>
              <div className="mt-4 text-purple-600 group-hover:text-purple-700 font-medium">
                Have a Script? →
              </div>
            </Link>
            
            <Link 
              href="/images" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-green-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">🎨</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">3. Scene Images</h3>
              <p className="text-slate-600 text-sm">
                Generate AI visuals that match your script scenes
              </p>
              <div className="mt-4 text-green-600 group-hover:text-green-700 font-medium">
                Create Visuals →
              </div>
            </Link>
          </div>
          
          <div className="mt-16 text-center">
            <h3 className="text-2xl font-semibold text-slate-900 mb-4">Complete Video Creation Pipeline</h3>
            <div className="flex justify-center items-center space-x-4 text-slate-500">
              <span className="bg-blue-50 border-blue-200 border px-4 py-2 rounded-lg text-blue-700">Script</span>
              <span>→</span>
              <span className="bg-purple-50 border-purple-200 border px-4 py-2 rounded-lg text-purple-700">Voice</span>
              <span>→</span>
              <span className="bg-green-50 border-green-200 border px-4 py-2 rounded-lg text-green-700">Images</span>
              <span>→</span>
              <span className="bg-orange-50 border-orange-200 border px-4 py-2 rounded-lg text-orange-700">Video</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
