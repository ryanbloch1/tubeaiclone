"use client";
import React from "react";
import styles from "./TitleBar.module.css";

type Props = {
  topic: string;
  setTopic: (v: string) => void;
  wordCount: number;
  onOpenWordModal: () => void;
  onOpenContextModal: () => void;
  onOpenStyleModal: () => void;
  loading?: boolean;
  canSubmit?: boolean;
};

export const TitleBar: React.FC<Props> = ({
  topic,
  setTopic,
  wordCount,
  onOpenWordModal,
  onOpenContextModal,
  onOpenStyleModal,
  loading,
  canSubmit,
}) => {
  return (
    <div className={styles.root}>
      <div className="flex items-center gap-2 pl-1 pr-3 text-slate-500">
        <button type="button" className={styles.iconBtn} title="Create New Style" onClick={onOpenStyleModal}>
          ⚙️
        </button>
        <span>🔍</span>
      </div>
      <input
        className="flex-1 bg-transparent px-2 py-2 outline-none text-white placeholder-slate-400"
        placeholder="Ten scary stories to fall asleep to"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
      />
      <div className="ml-3 flex items-center gap-3 text-slate-600">
        <button type="button" title="Style / Options" onClick={onOpenStyleModal} className="hover:text-slate-900 transition-colors">🎬</button>
        <button type="button" title="Additional Context" onClick={onOpenContextModal} className="hover:text-slate-900 transition-colors">✨</button>
        <button type="button" title="Word Count" onClick={onOpenWordModal} className="rounded-full border border-slate-300 px-3 py-1 text-sm hover:border-slate-400 transition-colors">
          {wordCount}
        </button>
        <button
          type="submit"
          disabled={!canSubmit || loading}
          className={styles.generate}
        >
          {loading ? "Generating..." : "Generate"}
        </button>
      </div>
    </div>
  );
};
