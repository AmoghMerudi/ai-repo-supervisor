export type BackendAnalyzeResponse = {
  summary: string;
  risks: string[];
  suggestions: string[];
  health_delta: number;
  baseline_score: number;
  semantic_score: number | null;
  structural_signals?: string[];
  semantic_insights?: string[];
  synthesis?: string | null;
};

export type PRAdapterOutput = {
  summaryText: string;
  primaryRisk: string | null;
  suggestedActions: string[];
  baselineRiskLabel: "Low" | "Medium" | "High";
  semanticRiskLabel: "Low" | "Medium" | "High" | null;
  healthDelta: number;
  healthDeltaLabel: "Improved" | "Declined" | "No change";
};

const riskLabelFromScore = (score: number) => {
  if (score > 85) {
    return "Low";
  }
  if (score >= 65) {
    return "Medium";
  }
  return "High";
};

export const getHealthLabelFromScore = (
  score: number
): "Healthy" | "At Risk" | "Critical" => {
  if (score > 85) {
    return "Healthy";
  }
  if (score >= 65) {
    return "At Risk";
  }
  return "Critical";
};

export const adaptPRAnalysis = (
  response: BackendAnalyzeResponse
): PRAdapterOutput => {
  const summaryText = response.summary?.trim() || "No summary available.";
  const primaryRisk = response.risks?.length ? response.risks[0] : null;
  const suggestedActions =
    response.suggestions?.length > 0
      ? response.suggestions
      : ["No immediate actions suggested."];

  const healthDeltaLabel =
    response.health_delta > 0
      ? "Improved"
      : response.health_delta < 0
        ? "Declined"
        : "No change";

  return {
    summaryText,
    primaryRisk,
    suggestedActions,
    baselineRiskLabel: riskLabelFromScore(response.baseline_score),
    semanticRiskLabel:
      response.semantic_score === null
        ? null
        : riskLabelFromScore(response.semantic_score),
    healthDelta: response.health_delta,
    healthDeltaLabel,
  };
};
