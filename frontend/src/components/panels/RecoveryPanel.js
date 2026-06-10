"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, ArrowRight, CheckCircle2, ChevronRight, Circle,
  Compass, Lightbulb, Loader2, Target, Trophy, XCircle,
} from "lucide-react";
import { BentoCard, Eyebrow, Button, StatusPill } from "@/components/ui";
import { Celebration } from "@/components/Celebration";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/cx";

function toPercent(score) {
  return Math.round((score ?? 0) * 100);
}

const GAP_TONE = {
  "[CRITICAL GAP]": { tone: "bad", icon: AlertTriangle, label: "Critical gap" },
  "[WEAK]": { tone: "warn", icon: Target, label: "Weak spot" },
};

const DIFFICULTY_LABEL = {
  conceptual: "Conceptual",
  "applied-diagnosis": "Applied diagnosis",
  "synthesis-application": "Synthesis and application",
};

export function RecoveryPanel({ profileId, onGraded }) {
  const [phase, setPhase] = useState("loading");
  const [week, setWeek] = useState(null);
  const [status, setStatus] = useState(null);
  const [sitting, setSitting] = useState(null);
  const [question, setQuestion] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(1);
  const [selected, setSelected] = useState(null);
  const [locking, setLocking] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [celebrateVariant, setCelebrateVariant] = useState(null);

  const finishingRef = useRef(false);

  const loadStatus = useCallback(async () => {
    setError(null);
    try {
      const board = await api.get(`/weekly-test/${profileId}/board`);
      const flagged = (board.weeks || []).find((row) => row.recovery_triggered);
      if (!flagged) {
        setPhase("hidden");
        return;
      }
      setWeek(flagged.week);
      const data = await api.get(`/recovery/${profileId}/${flagged.week}/status`);
      setStatus(data);
      setPhase(data.triggered ? "summary" : "hidden");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not read this plan's recovery status just now.");
      setPhase("hidden");
    }
  }, [profileId]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  async function beginOrResume() {
    if (week === null) return;
    setStarting(true);
    setError(null);
    try {
      const data = await api.post(`/recovery/${profileId}/${week}/start`, {});
      if (data.message) {
        await loadStatus();
        return;
      }
      finishingRef.current = false;
      setSitting(data);
      setQuestion(data.next_question);
      setQuestionIndex(data.question_index);
      setSelected(null);
      setResult(null);
      setPhase("active");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not open the recovery check right now - try again shortly.");
    } finally {
      setStarting(false);
    }
  }

  async function lockInAnswer() {
    if (selected === null || !sitting || !question) return;
    setLocking(true);
    setError(null);
    try {
      const data = await api.post(`/recovery/${profileId}/answer`, {
        evaluation_id: sitting.evaluation_id, question_id: question.id, choice: selected,
      });
      if (data.finished) {
        finishingRef.current = true;
        setResult(data);
        setPhase("finished");
        if (data.celebrate) {
          setCelebrateVariant("balloons-and-sparks");
        }
        loadStatus();
        onGraded?.();
      } else {
        setQuestion(data.next_question);
        setQuestionIndex(data.question_index + 1);
        setSelected(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "That answer did not lock in - try once more.");
    } finally {
      setLocking(false);
    }
  }

  function backToSummary() {
    setPhase("summary");
    setSitting(null);
    setQuestion(null);
    setResult(null);
    setSelected(null);
    loadStatus();
  }

  if (phase === "loading") {
    return (
      <BentoCard className="flex items-center justify-center gap-2 py-10 text-sm text-cap-slate">
        <Loader2 className="h-4 w-4 animate-spin" /> Reading this plan's recovery status.
      </BentoCard>
    );
  }

  if (phase === "hidden" || !status) {
    return null;
  }

  return (
    <BentoCard className="flex flex-col gap-6 border-2 border-cap-vibrant/30">
      <Celebration active={Boolean(celebrateVariant)} variant={celebrateVariant || "confetti"} onDone={() => setCelebrateVariant(null)} />

      <div>
        <Eyebrow>Learning recovery - week {week}</Eyebrow>
        <h3 className="mt-2 font-display text-xl font-semibold text-cap-navy">A different kind of help, not another retake</h3>
        <p className="mt-2 text-sm leading-relaxed text-cap-slate">
          Three sittings of this week's checkpoint have now landed under half in a row, and that is
          the one pattern worth answering with something other than a fourth try at the same paper.
          What follows is a plain read of exactly which topics those three sittings keep tripping
          over, a short note on each one, and a short, weighted check that opens the next attempt
          once it clears.
        </p>
      </div>

      {error ? (
        <div className="rounded-2xl border border-signal-bad/30 bg-signal-bad/5 px-4 py-3 text-sm text-signal-bad">
          {error}
        </div>
      ) : null}

      {phase === "summary" ? (
        <SummaryView status={status} starting={starting} onBegin={beginOrResume} />
      ) : null}

      {phase === "active" && sitting && question ? (
        <EvalSitting
          sitting={sitting}
          question={question}
          questionIndex={questionIndex}
          selected={selected}
          onSelect={setSelected}
          onLockIn={lockInAnswer}
          locking={locking}
        />
      ) : null}

      {phase === "finished" && result ? (
        <EvalResult result={result} onBack={backToSummary} />
      ) : null}
    </BentoCard>
  );
}

function SummaryView({ status, starting, onBegin }) {
  const active = status.active;
  const report = status.weakness_report;
  const plan = status.remediation_plan;

  let cta = {
    label: "Build my diagnosis",
    helper: "This reads the last three sittings and lays out exactly where they went sideways - nothing has been scored yet, this step only builds the read-out.",
  };
  if (active) {
    if (status.passed) {
      cta = null;
    } else if (status.status === "in_progress") {
      cta = {
        label: "Resume the check",
        helper: "Pick back up exactly where that sitting left off - the questions stay as they were, answered ones included.",
      };
    } else if (status.status === "submitted") {
      cta = {
        label: "Try again with a fresh set",
        helper: "That sitting came in under the half-mark this gate runs on. The next one is built fresh against the same diagnosis - never the same nine questions twice, the same rule the checkpoint itself runs on.",
      };
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {!active ? (
        <div className="rounded-2xl border border-cap-line bg-cap-mist/40 px-4 py-5">
          <p className="text-sm leading-relaxed text-cap-slate">
            This path has just opened. The first step builds a plain read of what those three
            sittings actually showed - which topics keep coming up short, by how much, and a short
            note on each, all before any check begins.
          </p>
        </div>
      ) : (
        <>
          {report ? <WeaknessReport report={report} /> : null}
          {plan && plan.length ? <RemediationPlan plan={plan} /> : null}
          {status.passed ? (
            <div className="flex items-start gap-3 rounded-2xl border border-signal-good/30 bg-signal-good/5 px-4 py-3.5">
              <Trophy className="mt-0.5 h-4 w-4 shrink-0 text-signal-good" />
              <div>
                <p className="text-sm font-semibold text-cap-navy">This check is cleared.</p>
                <p className="mt-1 text-sm leading-relaxed text-cap-slate">
                  {status.feedback || "The next checkpoint attempt is open from the board above - back to the regular retake gate from here."}
                </p>
              </div>
            </div>
          ) : status.status === "submitted" ? (
            <div className="flex items-start gap-3 rounded-2xl border border-signal-warn/30 bg-signal-warn/5 px-4 py-3.5">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-signal-warn" />
              <div>
                <p className="text-sm font-semibold text-cap-navy">
                  {toPercent(status.score)} percent on the weighted scale - just short of the half-mark this gate runs on.
                </p>
                <p className="mt-1 text-sm leading-relaxed text-cap-slate">{status.feedback}</p>
              </div>
            </div>
          ) : null}
        </>
      )}

      {cta ? (
        <div className="flex flex-col items-start gap-3 rounded-2xl border border-cap-line bg-white px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-relaxed text-cap-slate sm:max-w-md">{cta.helper}</p>
          <Button onClick={onBegin} disabled={starting}>
            {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {cta.label} <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      ) : null}
    </div>
  );
}

function WeaknessReport({ report }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Target className="h-4 w-4 text-cap-vibrant" />
        <Eyebrow>Personalised weakness report</Eyebrow>
      </div>
      <p className="text-sm leading-relaxed text-cap-slate">{report.summary}</p>
      <div className="flex flex-col gap-2">
        {(report.topics || []).map((topic) => {
          const tone = GAP_TONE[topic.status] || { tone: "unknown", icon: Circle, label: topic.status || "Tracked" };
          const Icon = tone.icon;
          return (
            <div key={topic.rank} className="flex flex-col gap-2 rounded-xl border border-cap-line bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-cap-mist text-xs font-semibold text-cap-navy">
                  {topic.rank}
                </span>
                <p className="text-sm font-medium text-cap-navy">{topic.topicName}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-cap-slate">{topic.knowledgeGapScore} percent correct across those sittings</span>
                <StatusPill status={tone.tone}>
                  <Icon className="h-3.5 w-3.5" /> {tone.label}
                </StatusPill>
              </div>
            </div>
          );
        })}
      </div>
      {report.passingThreshold ? <p className="text-xs text-cap-slate">{report.passingThreshold}</p> : null}
    </div>
  );
}

function RemediationPlan({ plan }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-cap-vibrant" />
        <Eyebrow>Concept, contrast, analogy - one bite-sized lesson per gap</Eyebrow>
      </div>
      <div className="flex flex-col gap-2">
        {plan.map((entry, index) => (
          <div key={`${entry.topicName}-${index}`} className="rounded-xl border border-cap-line bg-white px-4 py-3.5">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold text-cap-navy">{entry.topicName}</p>
              <span className="text-xs font-medium uppercase tracking-[0.12em] text-cap-vibrant">Priority {entry.priority}</span>
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-cap-slate">{entry.biteSizedLesson}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvalSitting({ sitting, question, questionIndex, selected, onSelect, onLockIn, locking }) {
  const difficulty = DIFFICULTY_LABEL[question.difficulty] || question.difficulty;
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-cap-navy/30 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cap-line pb-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cap-vibrant">
          <Compass className="h-3.5 w-3.5" /> Recovery check - question {questionIndex} of {sitting.total_questions}
        </div>
        <div className="flex items-center gap-2 text-xs text-cap-slate">
          <span className="rounded-full border border-cap-line bg-cap-mist/60 px-3 py-1 font-medium text-cap-navy">{question.topic}</span>
          {difficulty ? <span className="rounded-full border border-cap-line px-3 py-1">{difficulty}</span> : null}
        </div>
      </div>

      <p className="font-display text-base font-semibold leading-relaxed text-cap-navy">{question.prompt}</p>

      <div className="grid gap-2">
        {(question.options || []).map((option) => {
          const isChosen = selected === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => onSelect(option)}
              className={cx(
                "flex items-start gap-3 rounded-xl border px-4 py-3 text-left text-sm leading-relaxed transition-colors",
                isChosen ? "border-cap-blue bg-cap-blue/5 text-cap-navy" : "border-cap-line text-cap-slate hover:border-cap-blue/50 hover:bg-cap-mist/50",
              )}
            >
              {isChosen ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cap-blue" /> : <Circle className="mt-0.5 h-4 w-4 shrink-0 text-cap-line" />}
              <span>{option}</span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-2 border-t border-cap-line pt-3 text-xs leading-relaxed text-cap-slate sm:flex-row sm:items-center sm:justify-between">
        <p className="sm:max-w-md">{sitting.weighting_note}</p>
        <Button onClick={onLockIn} disabled={selected === null || locking}>
          {locking ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Lock in this answer <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-cap-slate">{sitting.pass_criteria}</p>
    </div>
  );
}

function EvalResult({ result, onBack }) {
  const passed = Boolean(result.passed);
  return (
    <div className="flex flex-col gap-5">
      <div className={cx(
        "flex flex-col items-start gap-3 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between",
        passed ? "border-signal-good/30 bg-signal-good/5" : "border-signal-warn/30 bg-signal-warn/5",
      )}>
        <div>
          <StatusPill status={passed ? "good" : "warn"}>
            {passed ? <Trophy className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
            {passed ? "Cleared" : "Not yet at the half-mark"}
          </StatusPill>
          <p className="mt-2 font-display text-lg font-semibold text-cap-navy">{toPercent(result.score)} percent on the weighted scale</p>
          <p className="mt-1 text-sm leading-relaxed text-cap-slate">{result.feedback}</p>
        </div>
        <Button variant="secondary" onClick={onBack}>
          Back to the recovery summary
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        <Eyebrow>Where each answer landed</Eyebrow>
        {(result.scored_questions || []).map((entry, index) => (
          <div
            key={entry.question_id}
            className={cx(
              "rounded-xl border px-4 py-3 text-sm leading-relaxed",
              entry.is_correct ? "border-signal-good/30 bg-signal-good/5" : "border-signal-bad/25 bg-signal-bad/5",
            )}
          >
            <div className="flex items-start gap-2">
              {entry.is_correct ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-signal-good" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-signal-bad" />}
              <div className="min-w-0">
                <p className="font-medium text-cap-navy">
                  Q{index + 1}. {entry.prompt}
                  <span className="ml-2 text-xs font-normal text-cap-slate">{entry.topic} - weight {entry.weight}x</span>
                </p>
                <p className="mt-1 text-xs text-cap-slate">
                  Your answer: <span className="font-medium text-cap-ink">{entry.chosen || "left blank"}</span>
                  {!entry.is_correct ? <> - keyed answer: <span className="font-medium text-cap-ink">{entry.correct_option}</span></> : null}
                </p>
                {entry.explainer ? <p className="mt-1 text-xs text-cap-slate">{entry.explainer}</p> : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
