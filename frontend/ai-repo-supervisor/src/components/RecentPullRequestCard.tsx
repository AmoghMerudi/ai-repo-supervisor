"use client";

import { useState } from "react";

import {
  adaptPRAnalysis,
  type BackendAnalyzeResponse,
} from "@/src/adapters/prAdapter";

type RecentPullRequestCardProps = {
  title: string;
  analysis: BackendAnalyzeResponse;
};

const healthDeltaClass = (healthDelta: number) => {
  if (healthDelta > 0) {
    return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
  }
  if (healthDelta < 0) {
    return "bg-rose-500/15 text-rose-300 border-rose-500/30";
  }
  return "bg-neutral-800 text-neutral-300 border-neutral-700";
};

export default function RecentPullRequestCard({
  title,
  analysis,
}: RecentPullRequestCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const adapted = adaptPRAnalysis(analysis);

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-neutral-100">{title}</p>
          <p className="mt-1 text-sm text-neutral-400">
            {adapted.summaryText}
          </p>
          {adapted.primaryRisk && (
            <p className="mt-2 text-sm text-amber-200">
              {adapted.primaryRisk}
            </p>
          )}
        </div>
        <span
          className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${healthDeltaClass(
            adapted.healthDelta
          )}`}
        >
          {adapted.healthDelta > 0 ? "+" : ""}
          {adapted.healthDelta}
        </span>
      </div>

      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="mt-3 text-xs font-semibold uppercase tracking-widest text-blue-300 hover:text-blue-200"
      >
        {isExpanded ? "Hide details" : "View details"}
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-3 text-sm text-neutral-300">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
              Summary
            </p>
            <p className="mt-1">{adapted.summaryText}</p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
              Risks
            </p>
            <ul className="mt-1 list-disc space-y-1 pl-4">
              {(analysis.risks.length > 0
                ? analysis.risks
                : ["No significant risks detected."]
              ).map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-500">
              Suggested actions
            </p>
            <ul className="mt-1 list-disc space-y-1 pl-4">
              {adapted.suggestedActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
