"use client";

import { Activity } from "lucide-react";
import { Eyebrow } from "@/components/ui";

const AGENT_LABELS = {
  profiling_diagnostician: "Profiling Diagnostician",
  roadmap_architect: "Roadmap Architect",
  resource_curator: "Resource Curator",
  coach_adapter: "Coach & Adapter",
  output_validator: "Output Validator",
  mock_interviewer: "Mock Interviewer",
};

/**
 * The audit trail, surfaced - every traced step any agent has taken for
 * this learner, newest first, with the confidence score shown plainly next
 * to the claim it backs. This is the panel that answers "what has the
 * system actually done with my data" without making anyone go dig for it.
 */
export function ActivityPanel({ activity }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <Activity className="h-4 w-4 text-cap-blue" />
        <Eyebrow className="!mt-0">Audit trail</Eyebrow>
      </div>
      <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">What the agents have done so far</h3>
      <ol className="mt-4 space-y-2.5 max-h-96 overflow-y-auto scrollbar-thin pr-1">
        {activity.map((entry, index) => (
          <li key={`${entry.timestamp}-${index}`} className="flex items-start justify-between gap-4 rounded-xl border border-cap-line bg-white px-4 py-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold text-cap-blue">{AGENT_LABELS[entry.agent_name] || entry.agent_name}</p>
              <p className="mt-0.5 text-sm text-cap-ink">{entry.output_summary}</p>
              <p className="mt-1 text-[11px] text-cap-slate">
                {entry.action.replace(/_/g, " ")} · {new Date(entry.timestamp).toLocaleString()}
              </p>
            </div>
            <span className="shrink-0 rounded-full bg-cap-mist px-2.5 py-1 text-[11px] font-semibold text-cap-blue">
              {Math.round(entry.confidence_score * 100)}%
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
