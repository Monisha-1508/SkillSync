"use client";

import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";
import {
  Target,
  Map,
  BookOpen,
  RotateCcw,
  ShieldCheck,
  MessagesSquare,
  Flame,
  Trophy,
  TrendingUp,
  Layers,
  ArrowRight,
  Radar,
} from "lucide-react";
import { Button, BentoCard, Eyebrow, SectionHeading } from "@/components/ui";

const AGENTS = [
  {
    icon: Target,
    name: "Profiling Diagnostician",
    copy: "Reads your self-rated skills against the role you want and draws the gap map - what you have, what's assumed, what's missing - before anything gets planned.",
  },
  {
    icon: Map,
    name: "Roadmap Architect",
    copy: "Builds three week-by-week routes - safe, target, stretch - sized to the hours you actually have, not the hours a generic course assumes you do.",
  },
  {
    icon: BookOpen,
    name: "Resource Curator",
    copy: "Matches each milestone to free or paid material from a vetted corpus, and says plainly why a pick fits your budget and your level - not just that it exists.",
  },
  {
    icon: RotateCcw,
    name: "Coach & Adapter",
    copy: "Turns your logged weeks into a revision deck and an honest nudge, and when a week slips, proposes a re-plan you approve before anything changes.",
  },
  {
    icon: ShieldCheck,
    name: "Output Validator",
    copy: "Checks the plan it just helped build against your own deadline and hours before you ever see it - the system grading its own homework, on the record.",
  },
  {
    icon: MessagesSquare,
    name: "Mock Interviewer",
    copy: "Runs company-flavoured rounds against the milestones you've actually covered, and scores answers against what the role rubric expects - not a generic checklist.",
  },
];

const GAME_FEATURES = [
  {
    icon: Flame,
    title: "Streaks that mean something",
    copy: "Built from the weeks you logged, not a counter that resets if you blink. Miss one and the coach proposes a re-plan instead of breaking your momentum.",
  },
  {
    icon: Layers,
    title: "Three routes, one decision",
    copy: "Safe, target and stretch sit side by side with the same milestones laid out - so picking a pace is a five-second comparison, not a leap of faith.",
  },
  {
    icon: TrendingUp,
    title: "A feasibility score that argues back",
    copy: "Not a vibe - a number computed from your hours, your deadline and your blackout weeks, with the arithmetic shown so you can check it yourself.",
  },
  {
    icon: Trophy,
    title: "Interview rounds you can replay",
    copy: "Each mock round is scored against the rubric the role actually uses, with the reasoning kept so you can see exactly what moved the needle next time.",
  },
];

const STATS = [
  { value: "6", label: "agents, one traced pipeline" },
  { value: "3", label: "roadmap variants per learner" },
  { value: "100%", label: "of agent reasoning shown, not assumed" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />
      <StatsStrip />
      <AgentSection />
      <GameSection />
      <ClosingCTA />
      <Footer />
    </main>
  );
}

function Header() {
  const { isSignedIn, user, status } = useAuth();
  return (
    <header className="sticky top-0 z-30 border-b border-cap-line/70 bg-cap-cloud/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cap-blue text-white">
            <Radar className="h-5 w-5" strokeWidth={2.25} />
          </span>
          <span className="font-display text-lg font-semibold text-cap-navy">SkillSync AI</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-cap-slate md:flex">
          <a href="#agents" className="hover:text-cap-blue transition-colors">How it works</a>
          <a href="#game" className="hover:text-cap-blue transition-colors">What you get</a>
          {isSignedIn ? (
            <Link href="/plans" className="hover:text-cap-blue transition-colors">My plans</Link>
          ) : null}
        </nav>
        <div className="flex items-center gap-3">
          {status === "checking" ? (
            <span className="hidden text-xs text-cap-slate sm:inline">Checking your session...</span>
          ) : isSignedIn ? (
            <Link
              href="/plans"
              className="hidden items-center gap-2 rounded-full border border-cap-line bg-white px-3.5 py-2 text-sm font-medium text-cap-navy hover:border-cap-blue/50 sm:flex"
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cap-mist text-[11px] font-semibold text-cap-blue">
                {(user?.name || "?").trim().charAt(0).toUpperCase()}
              </span>
              {user?.name?.split(" ")[0] || "Account"}
            </Link>
          ) : (
            <Button href="/login" variant="ghost" className="hidden sm:inline-flex">
              Log in
            </Button>
          )}
          <Button href={isSignedIn ? "/onboarding" : "/login"} variant="primary">
            Build my plan
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const { isSignedIn } = useAuth();
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-16 md:pb-24 md:pt-24">
      <div className="grid items-center gap-12 md:grid-cols-2">
        <div className="animate-rise">
          <Eyebrow>Placement prep, mapped and explained</Eyebrow>
          <h1 className="mt-3 font-display text-4xl font-semibold leading-[1.08] text-cap-navy md:text-5xl">
            See exactly where you stand. Get a plan that fits your week.
            Watch the system show its work.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-cap-slate md:text-lg">
            Tell SkillSync AI the role you're chasing and the hours you actually
            have. It maps your skill gap against that role, drafts three
            week-by-week routes sized to your schedule, lines up the resources
            for each milestone, and keeps a running, readable trail of why it
            made every call - so the plan you follow is one you can question.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Button href={isSignedIn ? "/onboarding" : "/login?next=/onboarding"} variant="primary" className="px-6 py-3 text-base">
              Start your gap analysis
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button href="/dashboard" variant="secondary" className="px-6 py-3 text-base">
              Look at a sample dashboard
            </Button>
          </div>
          <p className="mt-4 text-xs text-cap-slate">
            {isSignedIn
              ? "You're signed in - building a plan adds it straight to your account."
              : "One free account, any number of plans - the demo login on the sign-in page gets you straight to a populated one."}
          </p>
        </div>
        <HeroPanel />
      </div>
    </section>
  );
}

function HeroPanel() {
  const rows = [
    { label: "Python", you: 60, role: 85, tone: "known" },
    { label: "Data Structures", you: 35, role: 80, tone: "inferred" },
    { label: "SQL", you: 45, role: 70, tone: "weak" },
    { label: "System Design", you: 10, role: 55, tone: "unknown" },
  ];
  return (
    <BentoCard className="animate-rise [animation-delay:120ms]">
      <div className="flex items-center justify-between">
        <p className="font-display text-sm font-semibold text-cap-navy">Gap map - Software Development Engineer</p>
        <span className="rounded-full bg-cap-mist px-2.5 py-1 text-[11px] font-semibold text-cap-blue">live preview</span>
      </div>
      <div className="mt-6 space-y-4">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="font-medium text-cap-ink">{row.label}</span>
              <span className="text-xs text-cap-slate">{row.you}% you - {row.role}% role bar</span>
            </div>
            <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-cap-mist">
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-cap-line"
                style={{ width: `${row.role}%` }}
              />
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-cap-blue animate-[countUp_0.8s_ease-out_both]"
                style={{ width: `${row.you}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="mt-6 border-t border-cap-line pt-4 text-xs leading-relaxed text-cap-slate">
        Each bar is two numbers, not one - where you rated yourself, and where
        the target role typically sits. The space between them is the plan.
      </p>
    </BentoCard>
  );
}

function StatsStrip() {
  return (
    <section className="border-y border-cap-line/70 bg-white/60">
      <div className="mx-auto grid max-w-6xl grid-cols-1 divide-y divide-cap-line/70 px-6 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        {STATS.map((stat) => (
          <div key={stat.label} className="flex flex-col items-center gap-1 px-6 py-8 text-center">
            <span className="font-display text-3xl font-semibold text-cap-blue">{stat.value}</span>
            <span className="text-sm text-cap-slate">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function AgentSection() {
  return (
    <section id="agents" className="mx-auto max-w-6xl px-6 py-20">
      <SectionHeading
        eyebrow="Six agents, one traced pipeline"
        title="Every step of your plan is somebody's job - and you can watch each one work"
        lead="Onboarding doesn't disappear into a spinner. It runs through six small, specialised agents in sequence, and the dashboard streams each one's reasoning - what it read, what it decided, how confident it was - as it happens."
      />
      <div className="bento-grid mt-10 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {AGENTS.map((agent, index) => (
          <BentoCard key={agent.name} className={`animate-rise`} style={{ animationDelay: `${index * 70}ms` }}>
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cap-mist text-cap-blue">
              <agent.icon className="h-5 w-5" strokeWidth={2} />
            </span>
            <h3 className="mt-4 font-display text-base font-semibold text-cap-navy">{agent.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-cap-slate">{agent.copy}</p>
          </BentoCard>
        ))}
      </div>
    </section>
  );
}

function GameSection() {
  return (
    <section id="game" className="bg-white/60 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <SectionHeading
          eyebrow="Built to keep you coming back"
          title="The mechanics that make a fourteen-week plan survive week three"
          lead="None of this is decoration bolted onto a study planner. The streaks, the routes, the score - each one is a direct readout of something the agents already computed, surfaced so progress feels like progress."
        />
        <div className="bento-grid mt-10 grid-cols-1 sm:grid-cols-2">
          {GAME_FEATURES.map((feature, index) => (
            <BentoCard key={feature.title} className="animate-rise flex gap-4" style={{ animationDelay: `${index * 70}ms` }}>
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cap-mist text-cap-blue">
                <feature.icon className="h-5 w-5" strokeWidth={2} />
              </span>
              <div>
                <h3 className="font-display text-base font-semibold text-cap-navy">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-cap-slate">{feature.copy}</p>
              </div>
            </BentoCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function ClosingCTA() {
  const { isSignedIn } = useAuth();
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div
        className="flex flex-col items-start gap-6 rounded-bento border border-cap-navy/40 p-6 text-white shadow-[0_8px_24px_-12px_rgba(11,31,51,0.45)] md:flex-row md:items-center md:justify-between md:p-7"
        style={{ background: "#001E3C" }}
      >
        <div>
          <h2 className="font-display text-2xl font-semibold md:text-3xl">Ready to see your own gap map?</h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/75">
            The intake form takes about three minutes. What comes back is a
            plan sized to your week, not a generic syllabus with your name on it -
            and it lands in your account, alongside any others you build later.
          </p>
        </div>
        <Link
          href={isSignedIn ? "/onboarding" : "/login?next=/onboarding"}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full px-6 py-3 text-base font-semibold transition-colors duration-200"
          style={{ background: "#ffffff", color: "#0070AD" }}
        >
          {isSignedIn ? "Build another plan" : "Create your account"}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-cap-line/70">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 text-sm text-cap-slate sm:flex-row">
        <span>SkillSync AI - built for the Capgemini hackathon track on AI-assisted learning.</span>
        <span className="text-cap-slate/70">Reasoning shown at every step, by design.</span>
      </div>
    </footer>
  );
}
