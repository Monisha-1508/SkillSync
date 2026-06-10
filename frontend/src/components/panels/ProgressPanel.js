"use client";

import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { CheckCircle2, CircleDashed, CircleDot, AlertTriangle, Clock3, Loader2, ListChecks, Lock, ArrowRight, TriangleAlert, X } from "lucide-react";
import { BentoCard, Eyebrow, Button } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

const STATUS_META = {
  completed: { label: "Completed", color: "#1f9d6f", icon: CheckCircle2, chip: "border-signal-good/40 bg-signal-good/10 text-signal-good" },
  partial: { label: "Partly done", color: "#17ABDA", icon: CircleDot, chip: "border-cap-vibrant/40 bg-cap-vibrant/10 text-cap-vibrant" },
  in_progress: { label: "In progress", color: "#e0a82e", icon: Clock3, chip: "border-signal-warn/40 bg-signal-warn/10 text-signal-warn" },
  missed: { label: "Missed", color: "#d8584f", icon: AlertTriangle, chip: "border-signal-bad/40 bg-signal-bad/10 text-signal-bad" },
  not_started: { label: "Not logged yet", color: "#cfd8e3", icon: CircleDashed, chip: "border-cap-line bg-cap-mist/60 text-cap-slate" },
};

const LOG_OPTIONS = [
  { event_type: "completed", label: "Mark complete", tone: "good" },
  { event_type: "partial", label: "Partly done", tone: "warn" },
];

const MISSED_OPTION = { event_type: "missed", label: "Missed it", tone: "bad" };

const LOG_FLOOR_PERCENT = 50;

export function ProgressPanel({ progress, profileId, roadmapId, onLogged }) {
  const donutData = [
    { name: "completed", value: progress.completed_weeks, color: STATUS_META.completed.color },
    { name: "remaining", value: Math.max(progress.total_weeks - progress.completed_weeks, 0), color: "#e3e9f1" },
  ];

  const barData = progress.weeks.map((week) => ({
    week: `W${week.week}`,
    hours: week.hours,
    status: week.status,
  }));

  return (
    <div className="space-y-6">
      <div className="bento-grid grid-cols-1 lg:grid-cols-3">
        <BentoCard className="flex flex-col items-center justify-center text-center">
          <Eyebrow>Overall progress</Eyebrow>
          <div className="relative mt-2 h-40 w-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  innerRadius={56}
                  outerRadius={74}
                  startAngle={90}
                  endAngle={-270}
                  stroke="none"
                >
                  {donutData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-display text-3xl font-semibold text-cap-navy">{progress.percent_complete}%</span>
              <span className="text-[11px] text-cap-slate">complete</span>
            </div>
          </div>
          <p className="mt-3 text-sm text-cap-slate">
            <span className="font-semibold text-cap-ink">{progress.completed_weeks}</span> of{" "}
            <span className="font-semibold text-cap-ink">{progress.total_weeks}</span> plan weeks logged as done
          </p>
        </BentoCard>

        <BentoCard className="lg:col-span-2">
          <Eyebrow>Hours scheduled, week by week</Eyebrow>
          <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">Where the plan put your time</h3>
          <div className="mt-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
                <CartesianGrid strokeDasharray="4 6" stroke="#e3e9f1" vertical={false} />
                <XAxis dataKey="week" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={{ stroke: "#e3e9f1" }} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={28} />
                <Tooltip
                  cursor={{ fill: "#eef3f8" }}
                  formatter={(value, _name, item) => [`${value}h scheduled · ${STATUS_META[item.payload.status]?.label || "not logged"}`, ""]}
                  contentStyle={{ borderRadius: 12, border: "1px solid #e3e9f1", fontSize: 12 }}
                />
                <Bar dataKey="hours" radius={[6, 6, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={index} fill={STATUS_META[entry.status]?.color || "#cfd8e3"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-cap-slate">
            {Object.entries(STATUS_META).map(([key, meta]) => (
              <span key={key} className="inline-flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: meta.color }} />
                {meta.label}
              </span>
            ))}
          </div>
        </BentoCard>
      </div>

      <BentoCard>
        <div className="flex items-center justify-between">
          <div>
            <Eyebrow>Log a week</Eyebrow>
            <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">Tell the plan what actually happened</h3>
          </div>
          <span className="flex items-center gap-1.5 text-xs text-cap-slate">
            <ListChecks className="h-3.5 w-3.5" />
            {progress.weeks.length} scheduled weeks
          </span>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-cap-slate">
          The order runs checkpoint first, log second: sit a week's proctored
          test from the weekly checkpoint tab, and clearing {LOG_FLOOR_PERCENT} percent
          is what unlocks "log this week" here - and opens the next week's resources
          right behind it. "Missed it" needs no quiz behind it; an honest miss is
          worth logging on its own, any time.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {progress.weeks.map((week) => (
            <WeekRow key={week.week} week={week} profileId={profileId} roadmapId={roadmapId} onLogged={onLogged} />
          ))}
        </div>
      </BentoCard>
    </div>
  );
}

function WeekRow({ week, profileId, roadmapId, onLogged }) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(null);
  const [error, setError] = useState(null);
  const [confirmMiss, setConfirmMiss] = useState(false);
  const [reflowResult, setReflowResult] = useState(null);

  const meta = STATUS_META[week.status] || STATUS_META.not_started;
  const Icon = meta.icon;
  const canLog = Boolean(week.log_unlocked) || week.status === "completed";
  const alreadyMissed = week.is_missed;

  async function logAs(eventType) {
    setPending(eventType);
    setError(null);
    try {
      await api.post(`/roadmap/${profileId}/progress`, {
        roadmap_id: roadmapId,
        week: week.week,
        event_type: eventType,
      });
      setOpen(false);
      onLogged?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not log that week - try again in a moment.");
    } finally {
      setPending(null);
    }
  }

  async function confirmAndReflow() {
    setPending("missed");
    setError(null);
    setConfirmMiss(false);
    try {
      await api.post(`/roadmap/${profileId}/progress`, {
        roadmap_id: roadmapId,
        week: week.week,
        event_type: "missed",
      });
      const result = await api.post(`/roadmap/${profileId}/reflow/${week.week}`, {});
      setReflowResult(result);
      setTimeout(() => {
        setReflowResult(null);
        onLogged?.();
      }, 4500);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not apply the reflow - try again in a moment.");
    } finally {
      setPending(null);
    }
  }

  if (alreadyMissed) {
    return (
      <div className="rounded-xl border border-dashed border-signal-bad/30 bg-signal-bad/5 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-2 text-sm font-medium text-cap-slate line-through">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-signal-bad/10 text-xs font-semibold text-signal-bad">
              W{week.week}
            </span>
            Missed
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-signal-bad/30 bg-signal-bad/10 px-2.5 py-1 text-[11px] font-medium text-signal-bad">
            <AlertTriangle className="h-3 w-3" />
            Content carried forward
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-cap-line bg-white px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm font-medium text-cap-ink">
          <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
            week.is_merged
              ? "bg-amber-50 text-amber-700"
              : "bg-cap-mist text-cap-blue"
          }`}>
            W{week.week}
          </span>
          {week.hours}h scheduled
          {week.is_merged ? (
            <span className="rounded-full border border-amber-300/60 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
              Merged
            </span>
          ) : null}
        </span>
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${meta.chip}`}>
          <Icon className="h-3 w-3" />
          {meta.label}
        </span>
      </div>
      {week.skill_ids.length ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {week.skill_ids.map((id) => (
            <span key={id} className="rounded-full border border-cap-line bg-cap-mist/50 px-2 py-0.5 text-[11px] text-cap-slate">
              {id}
            </span>
          ))}
        </div>
      ) : null}
      {week.is_merged && week.merged_from_weeks?.length > 0 ? (
        <p className="mt-1.5 text-[11px] text-amber-600 leading-relaxed">
          Carries content from missed week {week.merged_from_weeks.filter((w) => w !== week.week).join(", ")}
        </p>
      ) : null}

      {confirmMiss ? (
        <div className="mt-3 rounded-xl border border-signal-bad/25 bg-signal-bad/5 px-3.5 py-3 space-y-3">
          <div className="flex items-start gap-2.5">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-signal-bad" />
            <div>
              <p className="text-xs font-semibold text-cap-navy">Carry this week forward?</p>
              <p className="mt-1 text-[11px] leading-relaxed text-cap-slate">
                Marking week {week.week} as missed will merge its {week.skill_ids.length} skill(s)
                and {week.hours}h into the next scheduled week. This cannot be undone.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={confirmAndReflow}
              disabled={pending !== null}
              className="inline-flex items-center gap-1.5 rounded-lg bg-signal-bad px-3 py-1.5 text-xs font-semibold text-white hover:bg-signal-bad/90 disabled:opacity-60"
            >
              {pending === "missed" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ArrowRight className="h-3.5 w-3.5" />}
              Yes, carry it forward
            </button>
            <button
              type="button"
              onClick={() => setConfirmMiss(false)}
              className="text-xs text-cap-slate hover:text-cap-ink"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : reflowResult ? (
        <div className="mt-3 rounded-xl border border-cap-line bg-cap-mist/50 px-3.5 py-3 space-y-1.5">
          <p className="text-xs font-semibold text-cap-navy">Roadmap updated</p>
          <p className="text-[11px] leading-relaxed text-cap-slate">{reflowResult.reflow_summary}</p>
          {reflowResult.deadline_breach && !reflowResult.compression_applied ? (
            <p className="text-[11px] leading-relaxed text-signal-bad">{reflowResult.breach_message}</p>
          ) : reflowResult.compression_applied ? (
            <p className="text-[11px] leading-relaxed text-signal-warn">{reflowResult.breach_message}</p>
          ) : null}
        </div>
      ) : open ? (
        <div className="mt-3 space-y-2">
          <div className="flex flex-wrap gap-2">
            {LOG_OPTIONS.map((option) => (
              <Button
                key={option.event_type}
                variant="secondary"
                className="px-3 py-1.5 text-xs"
                disabled={pending !== null}
                onClick={() => logAs(option.event_type)}
              >
                {pending === option.event_type ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                {option.label}
              </Button>
            ))}
          </div>
          <button type="button" onClick={() => setOpen(false)} className="text-xs text-cap-slate hover:text-cap-blue">
            cancel
          </button>
        </div>
      ) : (
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <button
            type="button"
            onClick={() => canLog && setOpen(true)}
            disabled={!canLog}
            title={canLog ? undefined : `Sit this week's checkpoint and clear ${LOG_FLOOR_PERCENT} percent first - that is what opens this up.`}
            className={`inline-flex items-center gap-1.5 text-xs font-medium ${
              canLog ? "text-cap-blue hover:underline" : "cursor-not-allowed text-cap-slate/70"
            }`}
          >
            {!canLog ? <Lock className="h-3 w-3" /> : null}
            Log this week
          </button>
          <button
            type="button"
            onClick={() => setConfirmMiss(true)}
            disabled={pending !== null}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-signal-bad hover:underline disabled:cursor-not-allowed disabled:opacity-60"
          >
            {MISSED_OPTION.label}
          </button>
        </div>
      )}
      {!canLog && !confirmMiss && !reflowResult ? (
        <p className="mt-1.5 text-[11px] leading-relaxed text-cap-slate">
          Sit this week's checkpoint from the weekly checkpoint tab and score {LOG_FLOOR_PERCENT} percent or
          higher - that is what unlocks "log this week" and opens the next week's resources behind it.
        </p>
      ) : null}
      {error ? <p className="mt-2 text-xs text-signal-bad">{error}</p> : null}
    </div>
  );
}
