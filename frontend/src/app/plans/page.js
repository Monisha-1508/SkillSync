"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Radar,
  ArrowRight,
  Plus,
  Loader2,
  AlertTriangle,
  Clock,
  Calendar,
  Gauge,
  History,
  LogOut,
  CheckCircle2,
} from "lucide-react";
import { Button, BentoCard, Eyebrow, StatusPill } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";

const PLACEMENT_LABELS = {
  general: "General placement prep",
  tcs_nqt: "TCS NQT",
  infytq: "Infosys InfyTQ",
  wipro_nlth: "Wipro NLTH",
  cap_exceller: "Capgemini Exceller",
};

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

/**
 * The "ultrakeeper" view - one account, every plan it has ever built, each
 * carrying its own progress so a returning learner can tell at a glance
 * which one needs attention before they open any of them. This is also
 * where "build another plan" lives, because customising a plan to a new
 * goal should never mean losing the one already in motion.
 */
export default function PlansHubPage() {
  const router = useRouter();
  const { status, isSignedIn, user, logout } = useAuth();
  const [plans, setPlans] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (status === "signed-out") router.replace("/login?next=/plans");
  }, [status, router]);

  useEffect(() => {
    if (!isSignedIn) return;
    api
      .get("/profiles/mine")
      .then(setPlans)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Could not load your plans just now."));
  }, [isSignedIn]);

  if (status !== "signed-in") {
    return (
      <main className="flex min-h-screen items-center justify-center text-cap-slate">
        <Loader2 className="h-5 w-5 animate-spin" />
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-cap-line/70 pb-6">
        <div>
          <Link href="/" className="inline-flex items-center gap-2 text-xs font-medium text-cap-slate hover:text-cap-blue">
            <Radar className="h-3.5 w-3.5" />
            SkillSync AI
          </Link>
          <Eyebrow className="mt-2">Your account</Eyebrow>
          <h1 className="mt-1 font-display text-2xl font-semibold text-cap-navy">
            Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
          </h1>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-cap-slate">
            <History className="h-3.5 w-3.5" />
            Every plan you have built lives here, with its progress kept alongside it.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button href="/onboarding" variant="primary">
            <Plus className="h-4 w-4" />
            Build a new plan
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              logout();
              router.push("/");
            }}
          >
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </div>
      </header>

      <section className="mt-8">
        {error ? (
          <BentoCard className="border-signal-bad/30 bg-signal-bad/5">
            <p className="flex items-center gap-2 text-sm font-medium text-signal-bad">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
          </BentoCard>
        ) : plans === null ? (
          <div className="flex items-center gap-3 py-16 text-cap-slate">
            <Loader2 className="h-4 w-4 animate-spin" />
            Gathering your plans and their progress...
          </div>
        ) : plans.length === 0 ? (
          <EmptyHub />
        ) : (
          <div className="bento-grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3">
            {plans.map((plan) => (
              <PlanCard key={plan.id} plan={plan} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function EmptyHub() {
  return (
    <BentoCard className="flex flex-col items-center px-8 py-14 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cap-mist text-cap-blue">
        <Radar className="h-6 w-6" />
      </span>
      <h2 className="mt-4 font-display text-xl font-semibold text-cap-navy">No plans yet - this is where they will land</h2>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-cap-slate">
        Build your first plan and the six agents will map your gaps, draft a
        week-by-week roadmap and line up resources for it - then it will show
        up here, with its progress, every time you come back.
      </p>
      <Button href="/onboarding" variant="primary" className="mt-6">
        Build my first plan
        <ArrowRight className="h-4 w-4" />
      </Button>
    </BentoCard>
  );
}

function PlanCard({ plan }) {
  const placementLabel = PLACEMENT_LABELS[plan.placement_mode] || plan.placement_mode;
  const tone = plan.progress_percent >= 70 ? "good" : plan.progress_percent >= 35 ? "warn" : "unknown";

  return (
    <BentoCard className="flex flex-col">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Eyebrow>{placementLabel}</Eyebrow>
          <h3 className="mt-1 font-display text-lg font-semibold text-cap-navy">{plan.target_role}</h3>
          <p className="mt-0.5 text-xs text-cap-slate">for {plan.name}</p>
        </div>
        {plan.pending_replan ? (
          <StatusPill status="warn">
            <AlertTriangle className="h-3 w-3" />
            Re-plan pending
          </StatusPill>
        ) : plan.has_roadmap ? (
          <StatusPill status="good">
            <CheckCircle2 className="h-3 w-3" />
            Active
          </StatusPill>
        ) : (
          <StatusPill status="unknown">Building</StatusPill>
        )}
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between text-xs text-cap-slate">
          <span className="font-medium text-cap-navy">
            {plan.completed_weeks} of {plan.total_weeks} weeks logged
          </span>
          <span>{plan.progress_percent}% complete</span>
        </div>
        <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-cap-mist">
          <span
            className={`block h-full rounded-full ${
              tone === "good" ? "bg-signal-good" : tone === "warn" ? "bg-signal-warn" : "bg-cap-blue"
            }`}
            style={{ width: `${Math.max(plan.progress_percent, plan.progress_percent > 0 ? 6 : 0)}%` }}
          />
        </div>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 text-xs text-cap-slate">
        <div className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5 text-cap-blue" />
          {plan.weekly_hours}h / week
        </div>
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5 text-cap-blue" />
          {plan.deadline_weeks}-week runway
        </div>
        {plan.feasibility_score != null ? (
          <div className="flex items-center gap-1.5">
            <Gauge className="h-3.5 w-3.5 text-cap-blue" />
            {Math.round(plan.feasibility_score * 100)}% feasibility
          </div>
        ) : null}
        <div className="flex items-center gap-1.5">
          <History className="h-3.5 w-3.5 text-cap-blue" />
          started {formatDate(plan.created_at)}
        </div>
      </dl>

      <div className="mt-6 flex items-center justify-between border-t border-cap-line pt-4">
        <span className="text-xs text-cap-slate">
          {plan.selected_variant ? `${plan.selected_variant} route selected` : "route not chosen yet"}
        </span>
        <Button href={`/dashboard?profile=${plan.id}`} variant="secondary">
          Open plan
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </BentoCard>
  );
}
