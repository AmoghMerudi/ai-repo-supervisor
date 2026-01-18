import Link from "next/link";

import RecentPullRequestCard from "@/src/components/RecentPullRequestCard";
import type { BackendAnalyzeResponse } from "@/src/adapters/prAdapter";
import { getHealthLabelFromScore } from "@/src/adapters/prAdapter";
import { repoHealthMocks } from "@/src/mocks/repoHealthMocks";

type RepoSummary = {
  repo: string;
  current_health: number;
  avg_score: number;
  total_prs: number;
  recent?: RepoRecentEntry[];
};

type RepoRecentEntry = {
  pr_number: number;
  score: number;
  timestamp: string;
  author: string;
  overall_health: number;
};

type RepoHistoryEntry = {
  pr_number: number;
  pr_score: number;
  health_delta: number;
  overall_health?: number | null;
  reason?: string | null;
  author?: string | null;
  timestamp?: string | null;
};

const getBackendBaseUrls = () => {
  const base =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
  if (base.endsWith("/api")) {
    return [base];
  }
  return [base, `${base}/api`];
};

const fetchRepoSummary = async (repo: string): Promise<RepoSummary | null> => {
  const baseUrls = getBackendBaseUrls();
  for (const baseUrl of baseUrls) {
    try {
      const res = await fetch(
        `${baseUrl}/db/repo-summary?repo=${encodeURIComponent(repo)}`,
        { cache: "no-store" }
      );
      if (!res.ok) {
        continue;
      }
      return res.json();
    } catch {
      continue;
    }
  }
  return null;
};

const fetchRepoHistory = async (repo: string): Promise<RepoHistoryEntry[]> => {
  const baseUrls = getBackendBaseUrls();
  for (const baseUrl of baseUrls) {
    try {
      const res = await fetch(
        `${baseUrl}/db/health-history?repo=${encodeURIComponent(
          repo
        )}&limit=10`,
        { cache: "no-store" }
      );
      if (!res.ok) {
        continue;
      }
      const data = await res.json();
      return Array.isArray(data?.history) ? data.history : [];
    } catch {
      continue;
    }
  }
  return [];
};

export default async function RepoPage({
  params,
}: {
  params: { repo: string };
}) {
  const normalizedRepoName = decodeURIComponent(params.repo);
  const [repo, history] = await Promise.all([
    fetchRepoSummary(normalizedRepoName),
    fetchRepoHistory(normalizedRepoName),
  ]);
  const fallbackRepo =
    repoHealthMocks.find((item) => item.repo === normalizedRepoName) || null;
  const resolvedRepo = repo ?? fallbackRepo;

  if (!resolvedRepo) {
    return (
      <main className="relative min-h-screen overflow-hidden bg-neutral-950 px-6 py-10 text-neutral-100 sm:px-10">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-blue-600/20 blur-3xl" />
          <div className="absolute -bottom-48 right-0 h-80 w-80 rounded-full bg-purple-600/20 blur-3xl" />
        </div>
        <div className="relative mx-auto w-full max-w-4xl">
          <h1 className="text-2xl font-bold">Repo not found</h1>
          <p className="mt-2 text-neutral-400">
            We could not find a repo named &quot;
            {normalizedRepoName || "unknown"}&quot;.
          </p>

          <Link
            href="/dashboard"
            className="mt-4 inline-block text-blue-400 hover:underline"
          >
            Back to dashboard
          </Link>
        </div>
      </main>
    );
  }

  const currentHealth =
    typeof resolvedRepo.current_health === "number"
      ? resolvedRepo.current_health
      : 0;
  const healthLabel = getHealthLabelFromScore(currentHealth);

  const fallbackHistory: RepoHistoryEntry[] = (resolvedRepo.recent || []).map(
    (entry) => ({
      pr_number: entry.pr_number,
      pr_score: entry.score ?? 0,
      health_delta: 0,
      overall_health: entry.overall_health,
      reason: "",
      author: entry.author,
      timestamp: entry.timestamp,
    })
  );
  const historySource: RepoHistoryEntry[] =
    history.length > 0 ? history : fallbackHistory;

  const recentPrs = historySource.map((entry: RepoHistoryEntry) => {
    const risks = entry.reason ? entry.reason.split(",").filter(Boolean) : [];

    return {
      title: `PR #${entry.pr_number}`,
      analysis: {
        summary: `PR #${entry.pr_number} score ${entry.pr_score}`,
        risks,
        suggestions: [],
        health_delta: entry.health_delta,
      baseline_score:
        typeof entry.overall_health === "number" ? entry.overall_health : 0,
        semantic_score: null,
      } satisfies BackendAnalyzeResponse,
    };
  });

  return (
    <main className="relative min-h-screen overflow-hidden bg-neutral-950 px-6 py-10 text-neutral-100 sm:px-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-blue-600/20 blur-3xl" />
        <div className="absolute -bottom-48 right-0 h-80 w-80 rounded-full bg-purple-600/20 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.08),transparent_55%)]" />
      </div>

      <div className="relative mx-auto w-full max-w-5xl">
        <header className="mb-8">
          <Link
            href="/dashboard"
            className="text-xs font-semibold uppercase tracking-widest text-blue-300 hover:text-blue-200"
          >
            Back to dashboard
          </Link>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold sm:text-4xl">
              {resolvedRepo.repo}
            </h1>
            <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
              Health score {currentHealth.toFixed(1)}
            </span>
          </div>
          <p className="mt-2 text-sm text-neutral-300 sm:text-base">
            Repository health and recent activity
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-400">
              Current health
            </p>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-4xl font-bold">
                {currentHealth.toFixed(1)}
              </span>
              <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs font-semibold text-neutral-200">
                {healthLabel}
              </span>
            </div>
            <p className="mt-3 text-sm text-neutral-300">
              Avg PR score {resolvedRepo.avg_score.toFixed(1)} ·{" "}
              {resolvedRepo.total_prs} PRs
              tracked
            </p>

            <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
              <div className="flex items-center justify-between text-xs text-neutral-500">
                <span>y-axis: health score</span>
                <span>x-axis: time / PR no.</span>
              </div>
              <div className="mt-3 h-36 rounded-md border border-dashed border-neutral-700 bg-neutral-950/40" />
              <p className="mt-4 text-sm text-neutral-300">
                Reason for recent health: {historySource[0]?.reason || "N/A"}
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent Pull Requests</h2>
              <span className="text-xs text-neutral-500">
                {resolvedRepo.total_prs} total
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {recentPrs.length === 0 ? (
                <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-400">
                  No recent pull requests found yet.
                </div>
              ) : (
                recentPrs.map(
                  (pr: { title: string; analysis: BackendAnalyzeResponse }) => (
                  <RecentPullRequestCard
                    key={pr.title}
                    title={pr.title}
                    analysis={pr.analysis}
                  />
                  )
                )
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
} 