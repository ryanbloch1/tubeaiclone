"use client";
import React from 'react';

type Props = {
  scenesCount: number;
  readyCount: number;
  promptsReady: boolean;
  generating: boolean;
  currentScene: number | null;
  progress: number;
  onGenerateAll: () => void;
};

export default function GenerationControls({
  scenesCount,
  readyCount,
  promptsReady,
  generating,
  currentScene,
  progress,
  onGenerateAll,
}: Props) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Scene Analysis</h2>
          <p className="text-slate-600 text-sm">Found {scenesCount} scenes • Prompts {readyCount}/{scenesCount}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-500">Prompts</div>
          <div className="text-2xl font-bold text-blue-600">{readyCount}/{scenesCount}</div>
        </div>
      </div>

      {!generating && (
        <button
          onClick={onGenerateAll}
          disabled={!promptsReady}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-4 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg flex items-center justify-center space-x-2"
        >
          <span>🎨</span>
          <span>Generate All Scene Images</span>
        </button>
      )}

      {generating && (
        <div className="text-center">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
              <span className="text-blue-700 font-medium">Generating Scene {currentScene} Images...</span>
            </div>
            <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${Math.round(progress * 100)}%` }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


