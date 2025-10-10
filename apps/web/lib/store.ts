/**
 * Minimal Zustand Store - Production Ready
 * 
 * PERSISTS:
 * - currentProjectId: Which project user is working on
 * 
 * TEMPORARY (in-memory, NOT persisted):
 * - Compatibility shims for old pages
 * - Will be removed as pages migrate to Supabase
 * 
 * ALL DATA SHOULD COME FROM SUPABASE:
 * - Scripts, images, voiceovers → fetch from database
 * - Form inputs → component local state
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

// Compatibility types (NOT persisted, temporary)
type CompatibilityState = {
  // Script compat (remove after migration)
  topic: string;
  style: string;
  mode: 'script' | 'outline';
  temperature: number;
  wordCount: number;
  selection: string;
  extraContext: string;
  imageCount: number;
  videoLength: string;
  editableScript: string;
  setScriptState: (partial: Partial<CompatibilityState> | ((s: CompatibilityState) => Partial<CompatibilityState>)) => void;
  
  // Voiceover compat (remove after migration)
  rawScript: string;
  audioUrl: string | null;
  audioDataUrl: string | null;
  cameFromScript: boolean;
  setVoiceoverState: (partial: Partial<CompatibilityState> | ((s: CompatibilityState) => Partial<CompatibilityState>)) => void;
  
  // Images compat (remove after migration)
  scenes: Array<{ scene_number: number; text: string; description: string }>;
  images: Array<{ scene_number: number; prompt: string; status: 'pending' | 'generating' | 'completed' | 'failed'; image_url?: string; error?: string }>;
  scenePrompts: Array<{ scene_number: number; prompt: string | null; status: 'loading' | 'ready' | 'error' }>;
  generating: boolean;
  currentScene: number | null;
  cameFromVoiceover: boolean;
  imagesScriptHash: string | null;
  setImagesState: (partial: Partial<CompatibilityState> | ((s: CompatibilityState) => Partial<CompatibilityState>)) => void;
};

/**
 * Core Store State
 */
export type StoreState = {
  // Hydration flag
  hydrated: boolean;
  setHydrated: (value: boolean) => void;
  
  // Project ID (ONLY persisted data)
  currentProjectId: string | null;
  setCurrentProject: (id: string | null) => void;
} & CompatibilityState;

const initialState: StoreState = {
  hydrated: false,
  setHydrated: () => {},
  currentProjectId: null,
  setCurrentProject: () => {},
  
  // Compat state (NOT persisted)
  topic: '',
  style: '',
  mode: 'script',
  temperature: 0.7,
  wordCount: 500,
  selection: '',
  extraContext: '',
  imageCount: 10,
  videoLength: '1:00',
  editableScript: '',
  setScriptState: () => {},
  rawScript: '',
  audioUrl: null,
  audioDataUrl: null,
  cameFromScript: false,
  setVoiceoverState: () => {},
  scenes: [],
  images: [],
  scenePrompts: [],
  generating: false,
  currentScene: null,
  cameFromVoiceover: false,
  imagesScriptHash: null,
  setImagesState: () => {},
};

export const useVideoStore = create<StoreState>()(
  persist(
    (set) => ({
      ...initialState,
      setHydrated: (value) => set({ hydrated: value }),
      setCurrentProject: (id) => set({ currentProjectId: id }),
      
      // Compat setters (in-memory only)
      setScriptState: (partial) => set((state) => ({ ...state, ...(typeof partial === 'function' ? partial(state) : partial) })),
      setVoiceoverState: (partial) => set((state) => ({ ...state, ...(typeof partial === 'function' ? partial(state) : partial) })),
      setImagesState: (partial) => set((state) => ({ ...state, ...(typeof partial === 'function' ? partial(state) : partial) })),
    }),
    {
      name: "tubeai_store",
      // ⚡ ONLY persist currentProjectId - nothing else!
      partialize: (state) => ({
        currentProjectId: state.currentProjectId,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHydrated(true);
        }
      }
    }
  )
);


