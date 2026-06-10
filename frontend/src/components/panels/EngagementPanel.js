"use client";

import { Flame, TrendingUp, ClipboardCheck } from "lucide-react";
import { BentoCard, Eyebrow } from "@/components/ui";

export function EngagementPanel({ engagement }) {
  const { signals, nudge } = engagement;
  const stats = [
    { icon: TrendingUp, label: "Completion", value: `${Math.round(signals.completion_rate * 100)}%` },
    { icon: Flame, label: "Streak", value: `${signals.streak_weeks}w` },
    {
      icon: ClipboardCheck,
      label: "Last quiz",
      value: signals.recent_quiz_score === null ? "not yet" : `${Math.round(signals.recent_quiz_score * 100)}%`,
    },
  ];

  return (
    <BentoCard>
      <Eyebrow>Coach & Adapter</Eyebrow>
      <h3 className="mt-1 font-display text-base font-semibold text-cap-navy capitalize">
        Reading: {signals.mood.replace(/_/g, " ")}
      </h3>
      <div className="mt-4 grid grid-cols-3 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-cap-line bg-white px-3 py-2.5 text-center">
            <stat.icon className="mx-auto h-4 w-4 text-cap-blue" />
            <p className="mt-1 font-display text-lg font-semibold text-cap-navy">{stat.value}</p>
            <p className="text-[11px] text-cap-slate">{stat.label}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-relaxed text-cap-ink">{nudge}</p>
    </BentoCard>
  );
}
