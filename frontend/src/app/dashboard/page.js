"use client";

import { Suspense, useEffect, useMemo, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Radar,
  Map,
  BookOpen,
  RotateCcw,
  ShieldCheck,
  Activity,
  Loader2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  MessagesSquare,
  ClipboardCheck,
  Trophy,
  Award,
} from "lucide-react";
import { BentoCard, Button, Eyebrow, StatusPill } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { OnboardingTrace } from "@/components/OnboardingTrace";
import { AlertBanner } from "@/components/AlertBanner";
import { GapMapPanel } from "@/components/panels/GapMapPanel";
import { RoadmapPanel } from "@/components/panels/RoadmapPanel";
import { ResourcesPanel } from "@/components/panels/ResourcesPanel";
import { RevisionPanel } from "@/components/panels/RevisionPanel";
import { ValidationPanel } from "@/components/panels/ValidationPanel";
import { EngagementPanel } from "@/components/panels/EngagementPanel";
import { ActivityPanel } from "@/components/panels/ActivityPanel";
import { ProgressPanel } from "@/components/panels/ProgressPanel";
import { InterviewPanel } from "@/components/panels/InterviewPanel";
import { WeeklyTestPanel } from "@/components/panels/WeeklyTestPanel";
import { RecoveryPanel } from "@/components/panels/RecoveryPanel";

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardLoading />}>
      <DashboardScreen />
    </Suspense>
  );
}

function DashboardLoading() {
  return (
    <main className="flex min-h-screen items-center justify-center text-cap-slate">
      <Loader2 className="h-5 w-5 animate-spin" />
    </main>
  );
}

function DashboardScreen() {
  const params = useSearchParams();
  const router = useRouter();
  const profileId = params.get("profile");
  const isFresh = params.get("fresh") === "1";

  const [phase, setPhase] = useState(profileId ? (isFresh ? "building" : "loading") : "needs-profile");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async (id) => {
    try {
      const dashboard = await api.get(`/dashboard/${id}`);
      setData(dashboard);
      setPhase("ready");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not load this learner's dashboard.");
      setPhase("error");
    }
  }, []);

  useEffect(() => {
    if (!profileId) return;
    if (!isFresh) loadDashboard(profileId);
  }, [profileId, isFresh, loadDashboard]);

  if (phase === "needs-profile") return <NeedsProfile />;

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <DashboardHeader profile={data?.profile} profileId={profileId} />

      {phase === "ready" && data?.alerts ? <AlertBanner alerts={data.alerts} /> : null}

      {phase === "building" && (
        <OnboardingTrace
          profileId={profileId}
          onDone={() => {
            setPhase("loading");
            loadDashboard(profileId);
          }}
        />
      )}

      {phase === "loading" && (
        <div className="mt-10 flex items-center gap-3 text-cap-slate">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading the latest plan for this learner...
        </div>
      )}

      {phase === "error" && (
        <BentoCard className="mt-10 border-signal-bad/30 bg-signal-bad/5">
          <p className="flex items-center gap-2 text-sm font-medium text-signal-bad">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </p>
          <Button className="mt-4" variant="secondary" onClick={() => router.push("/onboarding")}>
            Go back to onboarding
          </Button>
        </BentoCard>
      )}

      {phase === "ready" && data && (
        <DashboardGrid data={data} profileId={profileId} onRefresh={() => loadDashboard(profileId)} />
      )}
    </main>
  );
}

function DashboardHeader({ profile, profileId }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cap-line/70 pb-6">
      <div>
        <a href="/" className="inline-flex items-center gap-2 text-xs font-medium text-cap-slate hover:text-cap-blue">
          <Radar className="h-3.5 w-3.5" />
          SkillSync AI
        </a>
        <Eyebrow className="mt-2">Live plan dashboard</Eyebrow>
        <h1 className="mt-1 font-display text-2xl font-semibold text-cap-navy">
          {profile ? `${profile.name}'s placement plan` : "Building your plan"}
        </h1>
        {profile ? (
          <p className="mt-1 text-sm text-cap-slate">
            Targeting <span className="font-medium text-cap-ink">{profile.target_role}</span>
            {profile.target_companies?.length ? (
              <> · {profile.target_companies.join(", ")}</>
            ) : null}
            {" · "}
            {profile.weekly_hours}h/week for {profile.deadline_weeks} weeks
          </p>
        ) : (
          <p className="mt-1 text-sm text-cap-slate">profile {profileId}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Button href="/plans" variant="ghost">
          My plans
        </Button>
        <Button href="/onboarding" variant="secondary">
          Build another plan
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}

function NeedsProfile() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center px-6 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cap-mist text-cap-blue">
        <Radar className="h-6 w-6" />
      </span>
      <h1 className="mt-4 font-display text-2xl font-semibold text-cap-navy">No learner selected yet</h1>
      <p className="mt-2 text-sm leading-relaxed text-cap-slate">
        The dashboard reads one learner's plan at a time. Build a profile through
        the intake form and it will land here automatically, fully wired up.
      </p>
      <Button href="/onboarding" variant="primary" className="mt-6">
        Start the intake form
        <ArrowRight className="h-4 w-4" />
      </Button>
    </main>
  );
}

const TABS = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "gap", label: "Gap map", icon: Radar },
  { id: "roadmap", label: "Roadmap", icon: Map },
  { id: "progress", label: "Progress", icon: TrendingUp },
  { id: "resources", label: "Resources", icon: BookOpen },
  { id: "revision", label: "Revision", icon: RotateCcw },
  { id: "interview", label: "Mock interview", icon: MessagesSquare },
  { id: "checkpoint", label: "Weekly checkpoint", icon: ClipboardCheck },
  { id: "validation", label: "Validation report", icon: ShieldCheck },
];

function DashboardGrid({ data, profileId, onRefresh }) {
  const [tab, setTab] = useState("overview");

  const summaryCards = useMemo(() => buildSummaryCards(data), [data]);

  return (
    <div className="mt-8">
      <div className="bento-grid grid-cols-2 sm:grid-cols-5">
        {summaryCards.map((card) => (
          <BentoCard key={card.label} className="flex flex-col gap-1 py-5">
            <span className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-cap-slate">
              <card.icon className="h-3.5 w-3.5" />
              {card.label}
            </span>
            <span className="font-display text-2xl font-semibold text-cap-navy animate-countUp">{card.value}</span>
            <span className="text-xs text-cap-slate">{card.hint}</span>
          </BentoCard>
        ))}
      </div>

      {data.gamification ? <GamificationBar gamification={data.gamification} /> : null}

      <nav className="mt-8 flex flex-wrap gap-2 border-b border-cap-line/70 pb-3">
        {TABS.map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              tab === item.id ? "bg-cap-blue text-white" : "text-cap-slate hover:bg-cap-mist"
            }`}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="mt-6">
        {tab === "overview" && <OverviewTab data={data} onJump={setTab} />}
        {tab === "gap" && <GapMapPanel gapMap={data.gap_map} />}
        {tab === "roadmap" && <RoadmapPanel roadmap={data.roadmap} projectSuggestions={data.project_suggestions} />}
        {tab === "progress" && (
          <ProgressPanel progress={data.progress} profileId={profileId} roadmapId={data.roadmap.id} onLogged={onRefresh} />
        )}
        {tab === "resources" && (
          <ResourcesPanel resourcePicks={data.resource_picks} curation={data.resource_curation} resourceLock={data.resource_lock} />
        )}
        {tab === "revision" && <RevisionPanel revision={data.revision} profileId={profileId} onReviewed={onRefresh} />}
        {tab === "interview" && <InterviewPanel profileId={profileId} targetRole={data.profile?.target_role} />}
        {tab === "checkpoint" && (
          <div className="flex flex-col gap-6">
            <WeeklyTestPanel profileId={profileId} onGraded={onRefresh} />
            <RecoveryPanel profileId={profileId} onGraded={onRefresh} />
          </div>
        )}
        {tab === "validation" && <ValidationPanel report={data.validation_report} />}
      </div>
    </div>
  );
}

function buildSummaryCards(data) {
  const { gap_map, roadmap, revision, validation_report, engagement, progress } = data;
  return [
    {
      label: "Skills covered",
      value: `${gap_map.counts.covered}/${gap_map.total}`,
      hint: `${gap_map.counts.gap} flagged as gaps right now`,
      icon: Radar,
    },
    {
      label: "Plan progress",
      value: `${progress.percent_complete}%`,
      hint: `${progress.completed_weeks} of ${progress.total_weeks} weeks logged done`,
      icon: TrendingUp,
    },
    {
      label: "Feasibility",
      value: `${Math.round((roadmap.feasibility_score ?? 0) * 100)}%`,
      hint: `${roadmap.selected_variant} route selected`,
      icon: Map,
    },
    {
      label: "Revision deck",
      value: `${revision.due_now}`,
      hint: `due now of ${revision.total_cards} cards total`,
      icon: RotateCcw,
    },
    {
      label: "Plan check",
      value: validation_report.overall_status === "pass" ? "Clear" : "Flagged",
      hint: (() => {
        const total = validation_report.checks.length;
        const passed = validation_report.checks.filter((check) => check.status === "pass").length;
        return `${passed} of ${total} checks passed`;
      })(),
      icon: validation_report.overall_status === "pass" ? CheckCircle2 : ShieldCheck,
    },
  ];
}

function GamificationBar({ gamification }) {
  const { points, level, badges } = gamification;
  const earned = badges.filter((badge) => badge.earned);
  const progressPercent = Math.round((level.progress_to_next ?? 1) * 100);

  return (
    <BentoCard className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cap-blue/10 text-cap-blue">
          <Trophy className="h-6 w-6" />
        </span>
        <div>
          <p className="font-display text-lg font-semibold text-cap-navy">{points} points - {level.name}</p>
          {level.next_floor ? (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="h-1.5 w-36 overflow-hidden rounded-full bg-cap-mist">
                <span className="block h-full rounded-full bg-cap-blue" style={{ width: `${progressPercent}%` }} />
              </span>
              <span className="text-xs text-cap-slate">{level.next_floor - points} to the next level</span>
            </div>
          ) : (
            <p className="mt-1 text-xs text-cap-slate">Top band reached on this track - keep the streak going.</p>
          )}
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {earned.length ? earned.map((badge) => (
          <span
            key={badge.id}
            title={badge.note}
            className="inline-flex items-center gap-1.5 rounded-full border border-signal-good/30 bg-signal-good/10 px-3 py-1.5 text-xs font-medium text-signal-good"
          >
            <Award className="h-3.5 w-3.5" /> {badge.label}
          </span>
        )) : (
          <span className="text-xs text-cap-slate">Badges unlock as modules, checkpoints and rounds get logged.</span>
        )}
      </div>
    </BentoCard>
  );
}

function OverviewTab({ data, onJump }) {
  return (
    <div className="bento-grid grid-cols-1 lg:grid-cols-3">
      <BentoCard className="lg:col-span-2">
        <SectionLabel icon={Radar} label="Gap map summary" onJump={() => onJump("gap")} />
        <p className="mt-3 text-sm leading-relaxed text-cap-ink">{data.gap_map.summary}</p>
        <p className="mt-3 text-xs text-cap-slate">
          <span className="font-semibold text-cap-ink">{data.gap_map.disclosure.label}: </span>
          {data.gap_map.disclosure.message}
        </p>
      </BentoCard>

      <EngagementPanel engagement={data.engagement} />

      <BentoCard>
        <SectionLabel icon={Map} label="Selected route" onJump={() => onJump("roadmap")} />
        <p className="mt-3 text-sm leading-relaxed text-cap-ink">
          {data.roadmap.feasibility_explanation}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.keys(data.roadmap.variants).map((key) => (
            <StatusPill key={key} status={key === data.roadmap.selected_variant ? "good" : "unknown"}>
              {key}{key === data.roadmap.selected_variant ? " · active" : ""}
            </StatusPill>
          ))}
        </div>
      </BentoCard>

      <BentoCard className="lg:col-span-2">
        <SectionLabel icon={ShieldCheck} label="Output validator's sign-off" onJump={() => onJump("validation")} />
        <ValidationPanel report={data.validation_report} compact />
      </BentoCard>

      <BentoCard className="lg:col-span-3">
        <ActivityPanel activity={data.recent_activity} />
      </BentoCard>
    </div>
  );
}

export function SectionLabel({ icon: Icon, label, onJump }) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-2 text-sm font-semibold text-cap-navy">
        <Icon className="h-4 w-4 text-cap-blue" />
        {label}
      </span>
      {onJump ? (
        <button onClick={onJump} className="text-xs font-medium text-cap-blue hover:underline">
          View full panel
        </button>
      ) : null}
    </div>
  );
}
