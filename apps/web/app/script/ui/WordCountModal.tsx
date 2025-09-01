"use client";
import React, { useState, useEffect } from "react";
import styles from "./WordCountModal.module.css";

type WordCountModalProps = {
  open: boolean;
  wordCount: number;
  onClose: () => void;
  onSave: (value: number) => void;
};

export const WordCountModal: React.FC<WordCountModalProps> = ({ open, wordCount, onClose, onSave }) => {
  const [value, setValue] = useState<number>(wordCount);
  useEffect(() => setValue(wordCount), [wordCount]);
  if (!open) return null;
  return (
    <div className={styles.root}>
      <div className={styles.content}>
        <h2 className={styles.title}>Set Target Word Count</h2>
        <div className={styles.inputContainer}>
          <label htmlFor="wordCount" className={styles.label}>
            Word Count
          </label>
          <input
            type="number"
            id="wordCount"
            className={styles.input}
            value={value}
            onChange={(e) => setValue(parseInt(e.target.value || "500", 10))}
          />
          <span className="text-sm text-gray-500">Actual word count may vary</span>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={onClose} className={styles.button}>
            Cancel
          </button>
          <button type="submit" className={styles.saveButton}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};
