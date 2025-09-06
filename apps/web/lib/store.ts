import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// Centralized app state for the multi-step video creation flow
// - Persisted with JSON in localStorage under key `tubeai_store`
// - `hydrated` flips to true after the store rehydrates on client
// - Pages subscribe to only the slices they need for minimal rerenders

type ScriptMode = "script" | "outline";

// Script page slice
// Only user-editable inputs + the full editableScript are stored here
// API results and transient UI booleans remain component-local
type ScriptState = {
  topic: string;
  style: string;
  mode: ScriptMode;
  temperature: number;
  wordCount: number;
  selection: string;
  extraContext: string;
  imageCount: number;
  videoLength: string;
  editableScript: string;
  setScriptState: (partial: Partial<Omit<ScriptState, "setScriptState">>) => void;
};

// Voiceover slice
// We keep the generated `audioUrl` and a simple navigation hint
type VoiceoverState = {
  rawScript: string;
  audioUrl: string | null;
  audioDataUrl?: string | null;
  cameFromScript: boolean;
  setVoiceoverState: (partial: Partial<Omit<VoiceoverState, "setVoiceoverState">>) => void;
};

// Types reused by Images slice
type Scene = {
  scene_number: number;
  text: string;
  description: string;
};

type ImageGeneration = {
  scene_number: number;
  prompt: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  image_url?: string;
  error?: string;
};

// Images slice
// Derived from the script: parsed scenes + per-scene generation state
type ImagesState = {
  scenes: Scene[];
  images: ImageGeneration[];
  generating: boolean;
  currentScene: number | null;
  cameFromVoiceover: boolean;
  setImagesState: (partial: Partial<Omit<ImagesState, "setImagesState">>) => void;
};

export type StoreState = {
  // True after persist rehydrates on client
  hydrated: boolean;
  setHydrated: (value: boolean) => void;
} & ScriptState & VoiceoverState & ImagesState;

const initialState: StoreState = {
  hydrated: false,
  setHydrated: () => {},
  // Script
  topic: "",
  style: "",
  mode: "script",
  temperature: 0.7,
  wordCount: 500,
  selection: "",
  extraContext: "",
  imageCount: 10,
  videoLength: "1:00",
  editableScript: "",
  setScriptState: () => {},
  // Voiceover
  rawScript: "",
  audioUrl: null,
  audioDataUrl: null,
  cameFromScript: false,
  setVoiceoverState: () => {},
  // Images
  scenes: [],
  images: [],
  generating: false,
  currentScene: null,
  cameFromVoiceover: false,
  setImagesState: () => {}
};

export const useVideoStore = create<StoreState>()(
  persist(
    (set, get) => ({
      ...initialState,
      setHydrated: (value) => set({ hydrated: value }),
      setScriptState: (partial) => set((state) => ({ ...state, ...partial })),
      setVoiceoverState: (partial) => set((state) => ({ ...state, ...partial })),
      setImagesState: (partial) => set((state) => ({ ...state, ...partial }))
    }),
    {
      name: "tubeai_store",
      storage: createJSONStorage(() => localStorage),
      // Persist only the user-facing slices; omit functions and flags
      partialize: (state) => ({
        topic: state.topic,
        style: state.style,
        mode: state.mode,
        temperature: state.temperature,
        wordCount: state.wordCount,
        selection: state.selection,
        extraContext: state.extraContext,
        imageCount: state.imageCount,
        videoLength: state.videoLength,
        editableScript: state.editableScript,
        rawScript: state.rawScript,
        audioUrl: state.audioUrl,
        audioDataUrl: state.audioDataUrl,
        cameFromScript: state.cameFromScript,
        scenes: state.scenes,
        images: state.images,
        generating: state.generating,
        currentScene: state.currentScene,
        cameFromVoiceover: state.cameFromVoiceover
      }),
      onRehydrateStorage: () => (state, error) => {
        // Mark store as ready after rehydration completes
        if (state) {
          state.setHydrated(true);
        }
      }
    }
  )
);


