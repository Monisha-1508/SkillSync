"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Loader2, AlertTriangle, Target, Map, BookOpen, RotateCcw, ShieldCheck } from "lucide-react";
import { BentoCard, Eyebrow } from "@/components/ui";
import { api } from "@/lib/api";

const AGENT_META = {
  profiling_diagnostician: { label: "Profiling Diagnostician", icon: Target },
  roadmap_architect: { label: "Roadmap Architect", icon: Map },
  resource_curator: { label: "Resource Curator", icon: BookOpen },
  coach_adapter: { label: "Coach & Adapter", icon: RotateCcw },
  output_validator: { label: "Output Validator", icon: ShieldCheck },
};

const AGENT_ORDER = Object.keys(AGENT_META);

export function OnboardingTrace({ profileId, onDone }) {
  const [steps, setSteps] = useState([]);
  const [status, setStatus] = useState("running");
  const [errorDetail, setErrorDetail] = useState(null);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    if (!profileId) return;
    const source = new EventSource(api.streamUrl(`/profiles/${profileId}/onboarding-stream`));

    source.addEventListener("step", (event) => {
      const payload = JSON.parse(event.data);
      setSteps((prev) => [...prev, payload]);
    });

    source.addEventListener("complete", () => {
      setStatus("done");
      source.close();
      window.setTimeout(() => doneRef.current?.(), 600);
    });

    source.addEventListener("error", (event) => {
      let detail = "The plan-building pipeline hit a snag.";
      try {
        detail = JSON.parse(event.data)?.detail || detail;
      } catch {
      }
      setStatus("error");
      setErrorDetail(detail);
      source.close();
    });

    return () => source.close();
  }, [profileId]);

  const completedAgents = new Set(steps.map((step) => step.agent));

  return (
    <BentoCard className="mt-10">
      <div className="flex items-center justify-between">
        <div>
          <Eyebrow>Building your plan, live</Eyebrow>
          <h2 className="mt-1 font-display text-lg font-semibold text-cap-navy">
            Six agents are working through your profile, in order
          </h2>
        </div>
        {status === "running" && <Loader2 className="h-5 w-5 animate-spin text-cap-blue" />}
        {status === "done" && <CheckCircle2 className="h-5 w-5 text-signal-good" />}
        {status === "error" && <AlertTriangle className="h-5 w-5 text-signal-bad" />}
      </div>

      <ol className="mt-6 space-y-3">
        {AGENT_ORDER.map((agentKey) => {
          const meta = AGENT_META[agentKey];
          const step = steps.find((entry) => entry.agent === agentKey);
          const isDone = completedAgents.has(agentKey);
          const isActive = !isDone && status === "running" && isNextAgent(agentKey, completedAgents);
          return (
            <li
              key={agentKey}
              className={`flex items-start gap-4 rounded-xl border px-4 py-3 transition-colors ${
                isDone
                  ? "border-signal-good/30 bg-signal-good/5"
                  : isActive
                    ? "border-cap-blue/40 bg-cap-mist"
                    : "border-cap-line bg-white"
              }`}
            >
              <span
                className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                  isDone ? "bg-signal-good/15 text-signal-good" : isActive ? "bg-cap-blue text-white animate-pulseRing" : "bg-cap-mist text-cap-slate"
                }`}
              >
                {isDone ? <CheckCircle2 className="h-4 w-4" /> : isActive ? <Loader2 className="h-4 w-4 animate-spin" /> : <meta.icon className="h-4 w-4" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-cap-navy">{meta.label}</p>
                {step ? (
                  <>
                    <p className="mt-1 text-sm leading-relaxed text-cap-ink">{step.output_summary}</p>
                    <p className="mt-1 text-xs text-cap-slate">
                      confidence {Math.round(step.confidence * 100)}% · {step.duration_ms}ms
                    </p>
                  </>
                ) : (
                  <p className="mt-1 text-xs text-cap-slate">
                    {isActive ? "working through your profile now..." : "waiting its turn"}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {status === "error" ? (
        <p className="mt-5 rounded-xl border border-signal-bad/30 bg-signal-bad/10 px-4 py-3 text-sm text-signal-bad">
          {errorDetail} Reloading this page will pick the run back up.
        </p>
      ) : null}
    </BentoCard>
  );
}

function isNextAgent(agentKey, completedAgents) {
  const index = AGENT_ORDER.indexOf(agentKey);
  return AGENT_ORDER.slice(0, index).every((earlier) => completedAgents.has(earlier));
}
