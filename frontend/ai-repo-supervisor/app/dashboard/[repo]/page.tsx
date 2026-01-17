"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { mockRepos } from "@/app/libs/mockRepos";
import RecentPullRequestCard from "@/src/components/RecentPullRequestCard";
import { getHealthLabelFromScore } from "@/src/adapters/prAdapter";

export default function RepoPage() {
  const params = useParams<{ repo?: string | string[] }>();
  const repoParam = params?.repo ?? "";
  const repoName = Array.isArray(repoParam) ? repoParam[0] : repoParam;
  const normalizedRepoName = decodeURIComponent(repoName);

  const repo = mockRepos.find((r) => r.name === normalizedRepoName);

  if (!repo) {
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

  const healthLabel = getHealthLabelFromScore(repo.health.baseline_score);

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
            <h1 className="text-3xl font-bold sm:text-4xl">{repo.name}</h1>
            <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300">
              Health score {repo.health.baseline_score.toFixed(1)}
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
                {repo.health.baseline_score.toFixed(1)}
              </span>
              <span className="rounded-full border border-neutral-700 px-3 py-1 text-xs font-semibold text-neutral-200">
                {healthLabel}
              </span>
            </div>
            <p className="mt-3 text-sm text-neutral-300">{repo.reason}</p>

            <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
              <div className="flex items-center justify-between text-xs text-neutral-500">
                <span>y-axis: health score</span>
                <span>x-axis: time / PR no.</span>
              </div>
              <div className="mt-3 h-36 rounded-md border border-dashed border-neutral-700 bg-neutral-950/40" />
              <p className="mt-4 text-sm text-neutral-300">
                Reason for recent health: {repo.reason}
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent Pull Requests</h2>
              <span className="text-xs text-neutral-500">
                {repo.prs.length} total
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {repo.prs.map((pr) => (
                <RecentPullRequestCard
                  key={pr.title}
                  title={pr.title}
                  analysis={pr.analysis}
                />
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
} 