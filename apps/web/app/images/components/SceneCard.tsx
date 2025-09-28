"use client";
import React from 'react';
import Image from 'next/image';

type PromptState = { status: 'loading' | 'ready' | 'error'; prompt: string | null };
type ImageState = { status: 'pending' | 'generating' | 'completed' | 'failed'; image_url?: string };

type Props = {
  sceneNumber: number;
  sceneText: string;
  promptState: PromptState | undefined;
  imageState: ImageState | undefined;
  onChangePrompt: (value: string) => void;
  onGenerate: () => void;
  disabled?: boolean;
};

export default function SceneCard({ sceneNumber, sceneText, promptState, imageState, onChangePrompt, onGenerate, disabled }: Props) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
      <div className="flex gap-6">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-slate-900">Scene {sceneNumber}</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              imageState?.status === 'completed' ? 'bg-green-100 text-green-800' :
              imageState?.status === 'generating' ? 'bg-blue-100 text-blue-800' :
              imageState?.status === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {imageState?.status || 'pending'}
            </span>
          </div>

          <div className="mb-4">
            <p className="text-sm text-slate-600 mb-2">Scene Text:</p>
            <p className="text-slate-800 text-sm bg-slate-50 p-3 rounded border">
              {sceneText.split('\n').slice(0, 3).join(' ') || 'No text available'}
            </p>
          </div>

          <div className="mb-4">
            <p className="text-sm text-slate-600 mb-2">Generated Prompt:</p>
            {promptState?.status === 'loading' && (
              <div className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-slate-600 text-sm flex items-center space-x-2">
                <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                <span>Generating prompt...</span>
              </div>
            )}
            {promptState?.status === 'error' && (
              <div className="w-full rounded-lg border border-red-200 bg-red-50 p-3 text-red-700 text-sm">
                Failed to generate prompt. You can type one manually below.
              </div>
            )}
            {promptState && promptState.status !== 'loading' && (
              <textarea
                className="w-full rounded-lg border border-blue-200 bg-blue-50 p-3 text-slate-800 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-y"
                rows={3}
                value={promptState.prompt || ''}
                onChange={(e) => onChangePrompt(e.target.value)}
              />
            )}
            <div className="mt-2 flex justify-end">
              <button onClick={onGenerate} disabled={disabled} className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm">
                Generate This Scene
              </button>
            </div>
          </div>
        </div>

        <div className="w-64 flex-shrink-0">
          <div className="aspect-square bg-slate-100 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
            {imageState?.status === 'completed' && imageState?.image_url ? (
              <Image src={imageState.image_url} alt={`Scene ${sceneNumber}`} width={256} height={256} className="w-full h-full object-cover rounded-lg" />
            ) : imageState?.status === 'generating' ? (
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
                <p className="text-slate-500 text-sm">Generating...</p>
              </div>
            ) : imageState?.status === 'failed' ? (
              <div className="text-center text-red-500">
                <div className="text-2xl mb-2">❌</div>
                <p className="text-sm">Generation Failed</p>
              </div>
            ) : (
              <div className="text-center text-slate-400">
                <div className="text-4xl mb-2">🎨</div>
                <p className="text-sm">Awaiting Generation</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


