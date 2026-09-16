import { getApiUrl, getHealth } from "@/lib/api";
import Link from "next/link";

export default async function HomePage() {
  let health: Awaited<ReturnType<typeof getHealth>> | null = null;
  let errorMessage: string | null = null;

  try {
    health = await getHealth();
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "The backend is unreachable.";
  }

  const isHealthy = health?.success === true;

  return (
    <main className="min-h-screen bg-canvas px-6 py-12 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-5xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6">
          <span className="text-2xl font-bold tracking-tight">AVault</span>
          <div className="flex items-center gap-5 text-sm">
            <span className="uppercase tracking-[0.2em] text-ink/55">Phase 2</span>
            <Link href="/login" className="font-bold text-signal">Log in</Link>
          </div>
        </nav>

        <section className="grid gap-12 py-20 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div>
            <p className="mb-5 text-sm font-bold uppercase tracking-[0.22em] text-signal">
              College AV room
            </p>
            <h1 className="max-w-3xl text-6xl leading-[0.95] tracking-tight sm:text-8xl">
              Lending, with a clear signal.
            </h1>
            <p className="mt-8 max-w-xl text-lg leading-8 text-ink/70">
              AVault is the foundation for reliable equipment lending, availability, and returns.
              Sign in or register to connect with the Django authentication API.
            </p>
          </div>

          <div className="border border-ink/15 bg-white p-7 shadow-[8px_8px_0_#d8f3e4]">
            <div className="flex items-center justify-between border-b border-ink/10 pb-5">
              <span className="text-sm font-bold uppercase tracking-[0.16em]">System check</span>
              <span
                className={`h-3 w-3 rounded-full ${isHealthy ? "bg-emerald-500" : "bg-signal"}`}
                aria-label={isHealthy ? "Connected" : "Disconnected"}
              />
            </div>
            <p className="mt-6 text-2xl leading-tight">
              {isHealthy ? "API and database connected" : "Backend connection unavailable"}
            </p>
            <p className="mt-3 text-sm leading-6 text-ink/65">
              {health?.message ?? errorMessage ?? "Start Django to run the health check."}
            </p>
            <dl className="mt-8 space-y-3 border-t border-ink/10 pt-5 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-ink/55">Endpoint</dt>
                <dd className="truncate font-mono text-xs">{getApiUrl()}/health/</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink/55">Database</dt>
                <dd>{health?.database ?? "waiting"}</dd>
              </div>
            </dl>
          </div>
        </section>
      </div>
    </main>
  );
}
