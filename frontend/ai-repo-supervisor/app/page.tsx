export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-neutral-950 text-neutral-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-blue-600/30 blur-3xl" />
        <div className="absolute -bottom-48 right-0 h-80 w-80 rounded-full bg-purple-600/25 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.08),transparent_55%)]" />
      </div>

      {/* Top-left brand */}
      <div className="absolute left-6 top-6 z-10 flex items-center gap-2">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/20 text-blue-300">
          P
        </span>
        <span className="text-sm font-semibold tracking-[0.25em] text-purple-200">
          PRISM
        </span>
      </div>

      {/* Centered hero */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 text-center">
        <span className="rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-blue-200">
          AI Repo Supervisor
        </span>

        {/* Main headline */}
        <h1 className="mt-5 text-balance text-4xl font-extrabold tracking-tight text-neutral-50 sm:text-6xl">
          See what your GitHub repos are really about.
        </h1>

        {/* Subtext */}
        <p className="mt-5 max-w-2xl text-pretty text-base text-neutral-300 sm:text-lg">
          PRISM maps architecture, ownership, and risk signals into a single
          dashboard so you can ship with clarity.
        </p>

        {/* CTA */}
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
          <a
            href="/dashboard"
            className="rounded-xl bg-blue-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-400"
          >
            Go to Dashboard
          </a>
        </div>

        <div className="mt-10 grid w-full max-w-3xl gap-4 text-left sm:grid-cols-3">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
            <h3 className="text-sm font-semibold text-neutral-100">Signals</h3>
            <p className="mt-2 text-xs text-neutral-400">
              Risk, change velocity, and ownership in one view.
            </p>
          </div>
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
            <h3 className="text-sm font-semibold text-neutral-100">Lineage</h3>
            <p className="mt-2 text-xs text-neutral-400">
              Trace dependencies and surface hidden coupling.
            </p>
          </div>
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
            <h3 className="text-sm font-semibold text-neutral-100">Focus</h3>
            <p className="mt-2 text-xs text-neutral-400">
              Align teams around the code that matters most.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}