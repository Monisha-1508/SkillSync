"use client";

import { CheckCircle2, AlertTriangle } from "lucide-react";
import { StatusPill } from "@/components/ui";

export function ValidationPanel({ report, compact = false }) {
  const flagged = report.checks.filter((check) => check.status !== "pass");
  const visible = compact ? (flagged.length ? flagged : report.checks.slice(0, 2)) : report.checks;

  return (
    <div className="mt-3">
      <div className="flex items-center gap-2">
        {report.overall_status === "pass" ? (
          <StatusPill status="good"><CheckCircle2 className="h-3 w-3" /> All checks passed</StatusPill>
        ) : (
          <StatusPill status="warn"><AlertTriangle className="h-3 w-3" /> Some checks were flagged</StatusPill>
        )}
        <span className="text-xs text-cap-slate">checked {new Date(report.checked_at).toLocaleString()}</span>
      </div>
      <ul className="mt-3 space-y-2">
        {visible.map((check) => (
          <li key={check.name} className="rounded-xl border border-cap-line bg-white px-3.5 py-2.5">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-cap-ink">{check.name}</span>
              <StatusPill status={check.status === "pass" ? "good" : check.status === "adjusted" ? "inferred" : "warn"}>
                {check.status}
              </StatusPill>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-cap-slate">{check.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
