import { useVideoStore } from "./store";

export function useHydrated(): boolean {
  // Store flips hydrated to true after persist rehydrates on client
  const hydrated = useVideoStore(s => s.hydrated);
  return hydrated;
}
