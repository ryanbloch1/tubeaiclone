export function sanitizeScriptForVoiceover(input: string): string {
  if (!input) return "";

  // Remove carriage returns and split into lines
  const lines = input.replace(/\r/g, "").split("\n");

  const cleanedLines: string[] = [];

  for (const rawLine of lines) {
    let line = rawLine;

    // strip common markdown emphasis
    line = line.replace(/\*\*|__/g, "");

    // Remove leading Title label
    line = line.replace(/^\s*Title\s*:?\s*/i, "");

    // Remove leading Scene/Chapter/Part headers like: "Scene 1 (0:00-0:30):" or "Scene 1:" (with/without dash)
    line = line.replace(/^\s*(Scene|Chapter|Part)\s*\d+\s*(\([^)]*\))?\s*[:—-]?\s*/i, "");

    // Remove speaker labels like: "Narrator:" or "HOST:"
    line = line.replace(/^\s*[A-Za-z][A-Za-z ]{2,}:\s+/, "");

    // Remove inline timestamps like (0:00-0:30)
    line = line.replace(/\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\)/g, "");

    // Remove plain timestamps like 0:00-0:30 (without parentheses)
    line = line.replace(/\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b/g, "");

    // Remove bracketed tags like [Music], [SFX], [beat]
    line = line.replace(/\[[^\]]+\]/g, "");

    // Remove parenthesized stage directions if the whole line is one
    const trimmed = line.trim();
    if (trimmed.startsWith("(") && trimmed.endsWith(")") && trimmed.length > 2) {
      continue;
    }

    // Remove URLs
    line = line.replace(/https?:\/\/\S+/g, "");

    // Collapse multiple spaces
    line = line.replace(/\s{2,}/g, " ").trim();

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


