"use client";
import React, { useState, useEffect } from "react";
import styles from "./ContextModal.module.css";

type ContextModalProps = {
  open: boolean;
  value: string;
  onClose: () => void;
  onSave: (txt: string) => void;
};

export const ContextModal: React.FC<ContextModalProps> = ({ open, value, onClose, onSave }) => {
  const [text, setText] = useState<string>(value);
  useEffect(() => setText(value), [value]);
  if (!open) return null;
  return (
    <div className={styles.root}>
      <div className={styles.content}>
        <h2 className={styles.title}>Add Extra Context / Instructions</h2>
        <div className={styles.inputContainer}>
          <label htmlFor="context" className={styles.label}>
            Context
          </label>
          <textarea
            id="context"
            className={styles.textArea}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>
        <form onSubmit={(e) => {
          e.preventDefault();
          onSave(text);
        }}>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className={styles.button}>
              Cancel
            </button>
            <button type="submit" className={styles.saveButton}>
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
