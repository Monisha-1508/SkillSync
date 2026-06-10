"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, CalendarDays, Clock, Compass, Hammer, Layers, Sparkles } from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { BentoCard, Eyebrow, StatusPill } from "@/components/ui";

const VARIANT_META = {
  safe: { label: "Safe", status: "good", copy: "The pace most likely to land on time even on a rough week.", color: "#1f9d6f" },
  target: { label: "Target", status: "inferred", copy: "The balanced route - the one most learners in this spot actually choose.", color: "#0070AD" },
  stretch: { label: "Stretch", status: "warn", copy: "Tight but possible if the hours hold every single week.", color: "#e0a82e" },
};

export function RoadmapPanel({ roadmap, projectSuggestions }) {
  const variantKeys = Object.keys(roadmap.variants);
  const [active, setActive] = useState(roadmap.selected_variant || variantKeys[0]);
  const variant = roadmap.variants[active];

  const compareData = useMemo(
    () => variantKeys.map((key) => {
      const data = roadmap.variants[key];
      return {
        key,
        label: VARIANT_META[key]?.label || key,
        hours: data.total_hours,
        weeks: data.milestone_count,
        skills: data.skill_count,
        feasibility: Math.round((data.feasibility?.score ?? 0) * 100),
      };
    }),
    [roadmap.variants, variantKeys],
  );

  const weekHours = useMemo(
    () => variant.milestones.filter((m) => !m.is_blackout).map((m) => ({ week: `W${m.week}`, hours: m.hours, skills: m.skill_ids.length })),
    [variant],
  );

  return (
    <div className="space-y-6">
      {projectSuggestions ? <ProjectSuggestionsCard suggestions={projectSuggestions} /> : null}

      <BentoCard>
        <Eyebrow>Three routes, side by side</Eyebrow>
        <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
          What changes between safe, target and stretch
        </h3>
        <p className="mt-1 text-xs text-cap-slate">
          Bars read against the left axis (total hours), the line against the
          right (feasibility score) - the same comparison the architect made
          before recommending one, drawn out so it takes a glance, not a read.
        </p>
        <div className="mt-4 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={compareData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="4 6" stroke="#e3e9f1" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={{ stroke: "#e3e9f1" }} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={32} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={32} />
              <Tooltip
                cursor={{ fill: "#eef3f8" }}
                formatter={(value, name) => [name === "feasibility" ? `${value}%` : `${value}${name === "hours" ? "h" : ""}`, name]}
                contentStyle={{ borderRadius: 12, border: "1px solid #e3e9f1", fontSize: 12 }}
              />
              <Bar yAxisId="left" dataKey="hours" radius={[6, 6, 0, 0]} barSize={42}>
                {compareData.map((entry) => (
                  <Cell key={entry.key} fill={VARIANT_META[entry.key]?.color || "#94a3b8"} fillOpacity={entry.key === active ? 1 : 0.4} />
                ))}
              </Bar>
              <Line yAxisId="right" type="monotone" dataKey="feasibility" stroke="#17ABDA" strokeWidth={2.5} dot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex flex-wrap gap-4 text-xs text-cap-slate">
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-cap-blue" />total hours (bars)</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-0.5 bg-cap-vibrant" />feasibility score (line)</span>
        </div>
      </BentoCard>

      <div className="bento-grid grid-cols-1 sm:grid-cols-3">
        {variantKeys.map((key) => {
          const meta = VARIANT_META[key] || { label: key, status: "unknown", copy: "" };
          const data = roadmap.variants[key];
          const isActive = active === key;
          const isSelected = roadmap.selected_variant === key;
          return (
            <button key={key} onClick={() => setActive(key)} className="text-left">
              <BentoCard className={isActive ? "border-cap-blue ring-2 ring-cap-blue/20" : ""}>
                <div className="flex items-center justify-between">
                  <StatusPill status={meta.status}>{meta.label}</StatusPill>
                  {isSelected ? <span className="text-[11px] font-semibold text-cap-blue">currently active</span> : null}
                </div>
                <p className="mt-3 font-display text-2xl font-semibold text-cap-navy">{data.total_hours}h</p>
                <p className="text-xs text-cap-slate">across {data.milestone_count} weeks · {data.skill_count} skills</p>
                <p className="mt-2 text-xs leading-relaxed text-cap-slate">{meta.copy}</p>
              </BentoCard>
            </button>
          );
        })}
      </div>

      <BentoCard>
        <div className="flex items-start justify-between gap-4">
          <div>
            <Eyebrow>Why this route looks the way it does</Eyebrow>
            <h3 className="mt-1 font-display text-base font-semibold text-cap-navy capitalize">{active} route - architect's rationale</h3>
          </div>
          <span className="flex items-center gap-1.5 rounded-full bg-cap-mist px-3 py-1.5 text-xs font-medium text-cap-blue">
            <Compass className="h-3.5 w-3.5" />
            feasibility {Math.round((variant.feasibility?.score ?? 0) * 100)}%
          </span>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-cap-ink">{variant.rationale}</p>
        {variant.feasibility?.explanation ? (
          <p className="mt-2 text-xs leading-relaxed text-cap-slate">{variant.feasibility.explanation}</p>
        ) : null}
      </BentoCard>

      <BentoCard>
        <Eyebrow>Week by week</Eyebrow>
        <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
          {active === roadmap.selected_variant ? "Active milestones" : `${active} route preview`}
        </h3>
        <p className="mt-1 text-xs text-cap-slate">
          The shape of the {active} route across its {weekHours.length} working
          weeks - taller bars are heavier weeks, so a glance here is the
          fastest way to spot where the load actually sits.
        </p>
        <div className="mt-4 h-44">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={weekHours} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="4 6" stroke="#e3e9f1" vertical={false} />
              <XAxis dataKey="week" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={{ stroke: "#e3e9f1" }} tickLine={false} interval={0} />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={28} />
              <Tooltip
                cursor={{ fill: "#eef3f8" }}
                formatter={(value, name) => [name === "hours" ? `${value}h scheduled` : `${value} skills`, ""]}
                contentStyle={{ borderRadius: 12, border: "1px solid #e3e9f1", fontSize: 12 }}
              />
              <Bar dataKey="hours" radius={[5, 5, 0, 0]} fill={VARIANT_META[active]?.color || "#0070AD"} fillOpacity={0.85} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <ol className="mt-4 space-y-3">
          {variant.milestones.map((milestone) => (
            <li
              key={milestone.week}
              className={`flex items-start gap-4 rounded-xl border px-4 py-3 ${
                milestone.is_blackout ? "border-dashed border-cap-line bg-cap-mist/40" : "border-cap-line bg-white"
              }`}
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cap-mist text-xs font-semibold text-cap-blue">
                W{milestone.week}
              </span>
              <div className="min-w-0 flex-1">
                {milestone.is_blackout ? (
                  <p className="flex items-center gap-2 text-sm text-cap-slate">
                    <CalendarDays className="h-4 w-4" />
                    Blackout week - {milestone.note || "kept clear on purpose"}
                  </p>
                ) : (
                  <>
                    <div className="flex flex-wrap gap-1.5">
                      {milestone.skill_ids.map((skillId) => (
                        <span key={skillId} className="rounded-full border border-cap-line bg-cap-mist/60 px-2.5 py-0.5 text-xs text-cap-ink">
                          {skillId}
                        </span>
                      ))}
                    </div>
                    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-cap-slate">
                      <Clock className="h-3.5 w-3.5" />
                      {milestone.hours}h scheduled this week
                    </p>
                  </>
                )}
              </div>
            </li>
          ))}
        </ol>
      </BentoCard>

      <LiveScheduleCard
        milestones={roadmap.active_milestones}
        replanLog={roadmap.replan_log}
      />
    </div>
  );
}

function LiveScheduleCard({ milestones, replanLog }) {
  const latestReflow = useMemo(() => {
    const entries = (replanLog || []).filter((e) => e.operation === "reflow");
    return entries.length ? entries[entries.length - 1] : null;
  }, [replanLog]);

  const hasUnresolvedBreach =
    latestReflow?.deadline_breach && !latestReflow?.compression_applied;

  const activeMilestones = useMemo(
    () => [...(milestones || [])].sort((a, b) => a.week - b.week),
    [milestones],
  );

  const hasReflowData = activeMilestones.some(
    (m) => m.is_missed || m.is_merged,
  );

  if (!hasReflowData && !latestReflow) return null;

  return (
    <BentoCard>
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow>Live schedule - after recovery reflow</Eyebrow>
          <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
            How the plan looks after carrying missed weeks forward
          </h3>
        </div>
        <span className="flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700">
          <Layers className="h-3.5 w-3.5" />
          Reflowed
        </span>
      </div>

      {hasUnresolvedBreach ? (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-signal-bad/30 bg-signal-bad/5 px-4 py-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-signal-bad" />
          <div className="min-w-0">
            <p className="text-xs font-semibold text-signal-bad">Deadline breach</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-cap-slate">
              {latestReflow.breach_message || "The reflowed plan exceeds your original deadline - consider extending your target date by one week."}
            </p>
          </div>
        </div>
      ) : latestReflow?.compression_applied ? (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-signal-warn/30 bg-signal-warn/10 px-4 py-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-signal-warn" />
          <div className="min-w-0">
            <p className="text-xs font-semibold text-cap-navy">Compression applied</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-cap-slate">
              {latestReflow.compression_detail || "Two lighter weeks were merged to keep the plan within your deadline."}
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-signal-good/30 bg-signal-good/10 px-4 py-3">
          <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-signal-good" />
          <p className="text-[11px] leading-relaxed text-cap-slate">
            {latestReflow?.reflow_summary || "Roadmap recovered - content carried forward, schedule fits the deadline."}
          </p>
        </div>
      )}

      <ol className="mt-5 space-y-2.5">
        {activeMilestones.map((milestone) => {
          if (milestone.is_blackout) {
            return (
              <li key={milestone.week} className="flex items-start gap-3 rounded-xl border border-dashed border-cap-line bg-cap-mist/40 px-4 py-2.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cap-mist text-xs font-semibold text-cap-slate">
                  W{milestone.week}
                </span>
                <p className="flex items-center gap-1.5 text-sm text-cap-slate">
                  <CalendarDays className="h-3.5 w-3.5" />
                  Blackout week
                </p>
              </li>
            );
          }
          if (milestone.is_missed) {
            return (
              <li key={milestone.week} className="flex items-start gap-3 rounded-xl border border-dashed border-signal-bad/30 bg-signal-bad/5 px-4 py-2.5 opacity-60">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-signal-bad/10 text-xs font-semibold text-signal-bad">
                  W{milestone.week}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-signal-bad line-through">Missed</p>
                  <p className="text-[11px] text-cap-slate">
                    {milestone.note || "Content carried forward to the next week."}
                  </p>
                </div>
              </li>
            );
          }
          if (milestone.is_merged) {
            return (
              <li key={milestone.week} className="flex items-start gap-3 rounded-xl border border-amber-300/50 bg-amber-50/60 px-4 py-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-xs font-semibold text-amber-700">
                  W{milestone.week}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-amber-300/60 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
                      Merged week
                    </span>
                    <span className="text-xs text-cap-slate">{milestone.hours}h</span>
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {(milestone.skill_ids || []).map((skillId) => (
                      <span key={skillId} className="rounded-full border border-amber-200 bg-white px-2.5 py-0.5 text-xs text-amber-800">
                        {skillId}
                      </span>
                    ))}
                  </div>
                  {milestone.merged_from_weeks?.length > 0 ? (
                    <p className="mt-1 text-[11px] text-amber-600">
                      Carries weeks {milestone.merged_from_weeks.join(" + ")}
                    </p>
                  ) : null}
                </div>
              </li>
            );
          }
          return (
            <li key={milestone.week} className="flex items-start gap-3 rounded-xl border border-cap-line bg-white px-4 py-2.5">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cap-mist text-xs font-semibold text-cap-blue">
                W{milestone.week}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap gap-1.5">
                  {(milestone.skill_ids || []).map((skillId) => (
                    <span key={skillId} className="rounded-full border border-cap-line bg-cap-mist/60 px-2.5 py-0.5 text-xs text-cap-ink">
                      {skillId}
                    </span>
                  ))}
                </div>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-cap-slate">
                  <Clock className="h-3.5 w-3.5" />
                  {milestone.hours}h scheduled
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </BentoCard>
  );
}

const DIFFICULTY_COPY = {
  beginner: { label: "Warm-up build", tone: "good" },
  intermediate: { label: "Portfolio piece", tone: "inferred" },
  advanced: { label: "Capstone", tone: "warn" },
};

function ProjectSuggestionsCard({ suggestions }) {
  const projects = suggestions?.projects || [];
  if (!projects.length) return null;

  return (
    <BentoCard className="border-cap-vibrant/30 bg-gradient-to-br from-cap-mist/70 to-white">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-cap-blue/10 text-cap-blue">
          <Sparkles className="h-5 w-5" />
        </span>
        <div>
          <Eyebrow>Roadmap cleared - what to build next</Eyebrow>
          <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
            Hands-on projects worth the next few weekends
          </h3>
          <p className="mt-1 text-xs leading-relaxed text-cap-slate">
            Every week on this plan is logged done, so the most useful thing left to add is
            evidence - something a reviewer can open and click through. These were matched
            against the exact tracks this roadmap covered, ordered from a gentle warm-up build
            up to a real capstone.
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {projects.map((project) => {
          const meta = DIFFICULTY_COPY[project.difficulty] || { label: project.difficulty, tone: "unknown" };
          return (
            <div key={project.title} className="flex flex-col rounded-2xl border border-cap-line bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <h4 className="font-display text-sm font-semibold text-cap-navy">{project.title}</h4>
                <StatusPill status={meta.tone}>{meta.label}</StatusPill>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-cap-ink">{project.summary}</p>
              <p className="mt-2 flex items-center gap-1.5 text-xs text-cap-slate">
                <Clock className="h-3.5 w-3.5" />
                About {project.estimated_hours}h end to end
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {project.stack.map((item) => (
                  <span key={item} className="rounded-full border border-cap-line bg-cap-mist/60 px-2.5 py-0.5 text-xs text-cap-ink">
                    {item}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-xs leading-relaxed text-cap-slate">{project.why}</p>
              <p className="mt-2 flex items-start gap-1.5 text-xs leading-relaxed text-cap-blue">
                <Hammer className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                Stretch goal: {project.stretch_goal}
              </p>
            </div>
          );
        })}
      </div>
    </BentoCard>
  );
}
