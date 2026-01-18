import type { BackendAnalyzeResponse } from "@/src/adapters/prAdapter";
import { sampleAnalyzeResponse } from "@/src/mocks/sampleAnalyzeResponse";

type RepoHealth = {
  baseline_score: number;
  semantic_score: number | null;
  health_delta: number;
};

type RepoPR = {
  title: string;
  analysis: BackendAnalyzeResponse;
};

type MockRepo = {
  name: string;
  reason: string;
  health: RepoHealth;
  prs: RepoPR[];
};

const authRiskResponse: BackendAnalyzeResponse = {
  ...sampleAnalyzeResponse,
  summary: "Token refresh logic updated to handle expired sessions.",
  risks: [
    "Authentication-related logic was modified, which is security-sensitive.",
  ],
  suggestions: ["Add tests for refresh-token expiry and retry flows."],
  health_delta: -3,
  baseline_score: 72,
  semantic_score: 84,
};

const billingResponse: BackendAnalyzeResponse = {
  ...sampleAnalyzeResponse,
  summary: "Billing service refactored for clearer ownership boundaries.",
  risks: [],
  suggestions: ["Verify integration tests still pass in staging."],
  health_delta: 1,
  baseline_score: 78,
  semantic_score: 55,
};

const uiResponse: BackendAnalyzeResponse = {
  ...sampleAnalyzeResponse,
  summary: "Dashboard layout spacing adjusted for readability.",
  risks: [],
  suggestions: ["Double-check responsive breakpoints on mobile."],
  health_delta: 2,
  baseline_score: 88,
  semantic_score: 42,
};

export const mockRepos: MockRepo[] = [
  {
    name: "auth-service",
    reason: "Large PRs and missing tests",
    health: {
      baseline_score: 72,
      semantic_score: 84,
      health_delta: -3,
    },
    prs: [
      {
        title: "Fix auth token refresh",
        analysis: authRiskResponse,
      },
      {
        title: "Refactor billing service",
        analysis: billingResponse,
      },
    ],
  },
  {
    name: "frontend-app",
    reason: "Consistent PR sizes and good test coverage",
    health: {
      baseline_score: 88,
      semantic_score: 42,
      health_delta: 2,
    },
    prs: [
      {
        title: "Improve dashboard layout",
        analysis: uiResponse,
      },
    ],
  },
];