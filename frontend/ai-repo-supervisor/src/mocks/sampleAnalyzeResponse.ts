import type { BackendAnalyzeResponse } from "@/src/adapters/prAdapter";

export const sampleAnalyzeResponse: BackendAnalyzeResponse = {
  summary: "This pull request makes small, focused changes.",
  risks: [
    "Authentication-related logic was modified, which is security-sensitive.",
  ],
  suggestions: ["Add or review tests covering authentication edge cases."],
  health_delta: 2,
  baseline_score: 98.2,
  semantic_score: 50,
};
