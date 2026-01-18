import Link from "next/link";

import { getHealthLabelFromScore } from "@/src/adapters/prAdapter";
import { repoHealthMocks } from "@/src/mocks/repoHealthMocks";

type RepoSummary = {
  repo: string;
  current_health: number;
  avg_score: number;
  total_prs: number;
  updated_at?: string | null;
};

const getStatusClass = (status: string) => {
  if (status === "Critical") {
    return "text-rose-400";
  }
  if (status === "At Risk") {
    return "text-yellow-400";
  }
  return "text-emerald-400";
};

const getBackendBaseUrls = () => {
  const base =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
  if (base.endsWith("/api")) {
    return [base];
  }
  return [base, `${base}/api`];
};

const fetchRepos = async (): Promise<RepoSummary[]> => {
  const baseUrls = getBackendBaseUrls();
  for (const baseUrl of baseUrls) {
    try {
      const res = await fetch(`${baseUrl}/db/repos`, {
        cache: "no-store",
      });
      if (!res.ok) {
        continue;
      }
      const data = await res.json();
      return Array.isArray(data?.repos) ? data.repos : [];
    } catch {
      continue;
    }
  }
  return [];
};

export default async function Dashboard() {
  const repos = await fetchRepos();
  const resolvedRepos = repos.length > 0 ? repos : repoHealthMocks;

  return (
    <main className="relative min-h-screen overflow-hidden bg-neutral-950 px-6 py-10 text-neutral-100 sm:px-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-blue-600/20 blur-3xl" />
        <div className="absolute -bottom-48 right-0 h-80 w-80 rounded-full bg-purple-600/20 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.08),transparent_55%)]" />
      </div>

      <div className="relative mx-auto w-full max-w-6xl">
        <header className="mb-8">
          <span className="rounded-full border border-blue-400/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-blue-200">
            Repository Overview
          </span>
          <h1 className="mt-4 text-3xl font-bold sm:text-4xl">Dashboard</h1>
          <p className="mt-2 text-sm text-neutral-300 sm:text-base">
            Track repository health, risk signals, and recent changes at a glance.
          </p>
        </header>

        <section className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {resolvedRepos.length === 0 ? (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6 text-sm text-neutral-400">
              No repository data available yet. Run an analysis to populate the
              dashboard.
            </div>
          ) : (
            resolvedRepos.map((repo) => {
              const currentHealth =
                typeof repo.current_health === "number" ? repo.current_health : 0;
              const status = getHealthLabelFromScore(currentHealth);

              return (
                <Link
                  key={repo.repo}
                  href={`/dashboard/${encodeURIComponent(repo.repo)}`}
                  className="group rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5 shadow-sm transition hover:-translate-y-1 hover:border-neutral-600 hover:bg-neutral-900"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-neutral-100">
                      {repo.repo}
                    </h2>
                    <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400">
                      {currentHealth.toFixed(1)}
                    </span>
                  </div>

                  <p
                    className={`mt-3 text-sm font-semibold ${getStatusClass(
                      status
                    )}`}
                  >
                    {status}
                  </p>

                  <p className="mt-2 text-sm text-neutral-400">
                    Avg PR score {repo.avg_score.toFixed(1)} · {repo.total_prs}{" "}
                    PRs tracked
                  </p>

                  <p className="mt-4 text-xs font-semibold uppercase tracking-widest text-neutral-500 transition group-hover:text-neutral-300">
                    View details →
                  </p>
                </Link>
              );
            })
          )}
        </section>
      </div>
    </main>
  );
}