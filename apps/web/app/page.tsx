"use client";

import { useAuth } from '@/components/auth/AuthProvider';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/projects');
    }
  }, [user, loading, router]);

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

  if (user) {
    // Show loading state while redirecting
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-emerald-50">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-5xl font-extrabold text-slate-900 mb-4">
            RealEstate Video Pro
          </h1>
          <p className="text-xl text-slate-600 mb-10">
            Turn your property listings into professional videos with AI-generated scripts,
            voiceovers, and visuals.
          </p>
          
          <div className="bg-white/80 backdrop-blur border border-slate-200 rounded-2xl p-8 max-w-md mx-auto shadow-lg">
            <h2 className="text-2xl font-semibold text-slate-900 mb-4">Get Started</h2>
            <p className="text-slate-600 mb-6">
              Sign in to start creating listing videos, neighborhood guides, and market updates.
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
