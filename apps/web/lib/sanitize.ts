export function sanitizeScriptForVoiceover(input: string): string {
  if (!input) return "";

  // Remove carriage returns and split into lines
  const lines = input.replace(/\r/g, "").split("\n");

  const cleanedLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    // Find the next non-empty line for better heading detection
    let nextNonEmpty = "";
    for (let k = i + 1; k < lines.length; k++) {
      const cand = lines[k].trim();
      if (cand.length > 0) {
        nextNonEmpty = cand;
        break;
      }
    }
    let line = rawLine;

    // strip common markdown emphasis
    line = line.replace(/\*\*|__/g, "");

    // Remove leading Title label
    line = line.replace(/^\s*Title\s*:?\s*/i, "");

    // Remove leading Scene/Chapter/Part headers like: "Scene 1 (0:00-0:30):" or "Scene 1:" (with/without dash)
    line = line.replace(/^\s*(Scene|Chapter|Part)\s*\d+\s*(\([^)]*\))?\s*[:—-]?\s*/i, "");

    // Drop scene separators like --- or ———
    if (/^\s*(-{3,}|—{2,})\s*$/.test(line)) {
      continue;
    }

    // If line is a visuals/stage-direction label (e.g., "Visuals:"), drop the whole line
    if (/^\s*(Visuals?|B[- ]?roll|Shot List)\s*:/i.test(line)) {
      continue;
    }

    // Special handling: keep only the text after Content/Narration labels
    const contentMatch = line.match(/^\s*(Content\s*\/\s*Narration|Narration|Content)\s*:??\s*(.*)$/i);
    if (contentMatch) {
      line = contentMatch[2] || "";
    }

    // Remove speaker labels like: "Narrator:" or "HOST:" (generic fallback)
    line = line.replace(/^\s*[A-Za-z][A-Za-z ]{2,}:\s+/, "");

    // Remove inline timestamps like (0:00-0:30)
    line = line.replace(/\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\)/g, "");

    // Remove plain timestamps like 0:00-0:30 (without parentheses)
    line = line.replace(/\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b/g, "");

    // Handle bracketed content: keep narration, drop pure visual/stage directions
    // Examples to KEEP: [Voiceover: "..."] [A narrator says: '...'] [Narration: ...]
    // Strategy: for each [ ... ] block
    //  - if contains voiceover/narrator/narration keywords, extract quoted text if present; otherwise take text after ':'
    //  - else drop the block
    line = line.replace(/\[[^\]]+\]/g, (block) => {
      const inner = block.slice(1, -1); // remove [ ]

      const isNarration = /(voice\s*over|voiceover|narrator|narration|voice over|the narrator says|a narrator says|voice:|narrator:)/i.test(inner);
      if (!isNarration) {
        return ""; // drop pure visuals like [Music], [SFX], camera directions, etc.
      }

      // Try to extract quoted content first
      const quoted = inner.match(/["']([^"']+)["']/);
      if (quoted && quoted[1]) {
        return ` ${quoted[1]} `;
      }

      // Otherwise, keep text after the first ':' if any
      const colonIdx = inner.indexOf(":");
      if (colonIdx >= 0 && colonIdx < inner.length - 1) {
        const after = inner.slice(colonIdx + 1).trim();
        return after ? ` ${after} ` : "";
      }

      // Fallback: if it contains the keywords but no quotes/colon, keep the inner as narration
      return ` ${inner} `;
    });

    // Remove parenthesized stage directions if the whole line is one
    const trimmed = line.trim();
    if (trimmed.startsWith("(") && trimmed.endsWith(")") && trimmed.length > 2) {
      continue;
    }

    // If this looks like a standalone scene title and the next line begins with a colon or a narration label, drop the title line
    const maybeTitle = line.trim();
    if (maybeTitle.length > 0) {
      const wordCount = maybeTitle.split(/\s+/).filter(Boolean).length;
      const looksLikeShortHeading =
        wordCount <= 8 && /[A-Za-z]/.test(maybeTitle) && !/[.!]$/.test(maybeTitle);
      const nextLooksLikeNarration =
        /^(Content\s*\/\s*Narration|Narration|Content)\s*:/i.test(nextNonEmpty) ||
        (nextNonEmpty.length > 0 && nextNonEmpty.split(/\s+/).length >= 8);
      if (looksLikeShortHeading && nextLooksLikeNarration) {
        continue; // drop heading before narration
      }
    }

    // Remove URLs
    line = line.replace(/https?:\/\/\S+/g, "");

    // Remove a leading colon from lines like ": Hello there"
    line = line.replace(/^\s*:\s*/, "");

    // Collapse multiple spaces
    line = line.replace(/\s{2,}/g, " ").trim();

    // Trim wrapping quotes if the entire line is quoted
    if ((line.startsWith('"') && line.endsWith('"')) || (line.startsWith("'") && line.endsWith("'"))) {
      line = line.slice(1, -1).trim();
    }

    if (line.length > 0) {
      cleanedLines.push(line);
    }
  }

  // Collapse multiple blank lines: join with single newlines
  return cleanedLines.join("\n\n").trim();
}

export type VideoLengthOption =
  | "0:30"
  | "1:00"
  | "2:00"
  | "3:00"
  | "5:00"
  | "10:00";

export function imageCountForVideoLength(option: VideoLengthOption): number {
  // Approximate 30s per scene
  switch (option) {
    case "0:30":
      return 1;
    case "1:00":
      return 2;
    case "2:00":
      return 4;
    case "3:00":
      return 6;
    case "5:00":
      return 10;
    case "10:00":
      return 20;
    default:
      return 10;
  }
}

