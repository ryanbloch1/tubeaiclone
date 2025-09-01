"use client";
import React, { useState } from "react";
import styles from "./StyleModal.module.css";

type StyleModalProps = {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string) => void;
};

export const StyleModal: React.FC<StyleModalProps> = ({ open, onClose, onCreate }) => {
  const [name, setName] = React.useState("");
  const [lang, setLang] = React.useState("English");
  const [voice, setVoice] = React.useState("Frederick");
  const [wordCount, setWordCount] = React.useState(500);
  const [refs, setRefs] = React.useState<string[]>([]);
  if (!open) return null;
  return (
    <div className={styles.root}>
      <div className={styles.content}>
        <h2 className={styles.title}>Create New Style</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onCreate(name);
          }}
        >
          <div className={styles.inputGroup}>
            <label htmlFor="styleName" className={styles.label}>
              Style Name
            </label>
            <input
              type="text"
              id="styleName"
              className={styles.input}
              placeholder="Style Name*"
              value={name}
              onChange={(e)=>setName(e.target.value)}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="language" className={styles.label}>
              Language
            </label>
            <select
              id="language"
              className={styles.input}
              value={lang}
              onChange={(e)=>setLang(e.target.value)}
            >
              <option>English</option>
              <option>Spanish</option>
              <option>French</option>
            </select>
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="voice" className={styles.label}>
              Voice
            </label>
            <select
              id="voice"
              className={styles.input}
              value={voice}
              onChange={(e)=>setVoice(e.target.value)}
            >
              <option>Frederick</option>
              <option>Alloy</option>
              <option>Samantha</option>
            </select>
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="wordCount" className={styles.label}>
              Target Word Count (Optional)
            </label>
            <input
              type="number"
              id="wordCount"
              className={styles.input}
              value={wordCount}
              onChange={(e)=>setWordCount(parseInt(e.target.value||"500",10))}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="referenceVideo" className={styles.label}>
              Reference Video URL (Optional)
            </label>
            <input
              type="url"
              id="referenceVideo"
              className={styles.input}
              placeholder={`Reference URL #${refs.length+1}`}
              onChange={(e)=>{
                const v=[...refs]; v[refs.length]=e.target.value; setRefs(v);
              }}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="instructions" className={styles.label}>
              Specific Instructions (Optional)
            </label>
            <textarea
              id="instructions"
              className={styles.textArea}
              placeholder="Specific instructions for the AI (e.g., 'Be concise, use simple language, avoid jargon')"
            />
          </div>
          <div className={styles.buttonGroup}>
            <button type="button" onClick={onClose} className={styles.button}>
              Cancel
            </button>
            <button type="submit" className={styles.saveButton}>
              Save Style
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
