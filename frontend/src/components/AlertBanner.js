"use client";

import { AlertTriangle, AlertOctagon, X } from "lucide-react";
import { useState } from "react";
import { cx } from "@/lib/cx";

const LEVEL_META = {
  critical: {
    icon: AlertOctagon,
    wrap: "border-signal-bad/35 bg-signal-bad/10",
    badge: "bg-signal-bad/15 text-signal-bad",
    label: "Needs attention",
  },
  warn: {
    icon: AlertTriangle,
    wrap: "border-signal-warn/35 bg-signal-warn/10",
    badge: "bg-signal-warn/15 text-signal-warn",
    label: "Worth a look",
  },
};

/**
 * The deadline-and-pace nudge the dashboard owes a learner before they go
 * looking for it themselves - both numbers it shows are arithmetic over rows
 * already in the database (see `_deadline_alerts`), not a guess dressed up
 * as urgency. Dismissing one only hides it for this visit; reopening the
 * dashboard re-reads the same honest comparison and shows it again if it is
 * still true, the same way a human coach would not let a real deadline go
 * unmentioned just because it was mentioned once already.
 */
export function AlertBanner({ alerts }) {
  const [dismissed, setDismissed] = useState(() => new Set());
  const visible = (alerts || []).filter((_, index) => !dismissed.has(index));
  if (visible.length === 0) return null;

  return (
    <div className="mt-6 space-y-3">
      {(alerts || []).map((alert, index) => {
        if (dismissed.has(index)) return null;
        const meta = LEVEL_META[alert.level] || LEVEL_META.warn;
        const Icon = meta.icon;
        return (
          <div key={index} className={cx("flex items-start gap-3 rounded-2xl border px-4 py-3.5", meta.wrap)}>
            <Icon className="mt-0.5 h-4 w-4 shrink-0 text-cap-ink" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={cx("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide", meta.badge)}>
                  {meta.label}
                </span>
                <p className="text-sm font-semibold text-cap-navy">{alert.title}</p>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-cap-slate">{alert.message}</p>
            </div>
            <button
              type="button"
              onClick={() => setDismissed((prev) => new Set(prev).add(index))}
              aria-label="Dismiss this alert"
              className="rounded-full p-1.5 text-cap-slate hover:bg-white/70 hover:text-cap-ink"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
