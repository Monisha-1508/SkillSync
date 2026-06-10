"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Lock, LockOpen, RotateCcw, BookOpen, CheckCircle2, XCircle, Circle,
  Clock, ShieldAlert, Maximize, Trophy, ChevronRight, Loader2, X,
  Brain, Zap, Code2, Layers, AlertTriangle, ChevronDown, ChevronUp,
} from "lucide-react";
import { BentoCard, Eyebrow, Button, StatusPill } from "@/components/ui";
import { GamificationReward } from "@/components/GamificationReward";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/cx";

const LOCK_COPY = {
  locked:            { label: "Locked",         tone: "unknown", icon: Lock         },
  ready:             { label: "Unlocked",        tone: "good",    icon: LockOpen     },
  retake_ready:      { label: "Retake open",     tone: "warn",    icon: RotateCcw    },
  revision_required: { label: "Revise to retry", tone: "weak",    icon: BookOpen     },
  cleared:           { label: "Cleared",         tone: "good",    icon: CheckCircle2 },
};

const BAND_COPY = {
  passed:  { label: "Passed",            tone: "good" },
  partial: { label: "Partially cleared", tone: "warn" },
  failed:  { label: "Not cleared",       tone: "bad"  },
};

const Q_TYPE_META = {
  "Conceptual":    { Icon: Brain,  label: "Conceptual",    cls: "border-cap-blue/30 bg-cap-blue/10 text-cap-blue"       },
  "Application":   { Icon: Zap,    label: "Application",   cls: "border-purple-400/30 bg-purple-50 text-purple-700"    },
  "Code Analysis": { Icon: Code2,  label: "Code Analysis", cls: "border-amber-400/30 bg-amber-50 text-amber-700"       },
  "Synthesis":     { Icon: Layers, label: "Synthesis",     cls: "border-emerald-400/30 bg-emerald-50 text-emerald-700" },
};

const DIFF_CLS = {
  Easy:   "border-emerald-300/60 bg-emerald-50 text-emerald-700",
  Medium: "border-amber-300/60 bg-amber-50 text-amber-700",
  Hard:   "border-red-300/60 bg-red-50 text-red-700",
};

const _RETRY_QUOTES = [
  "A score like this is not a verdict - it is a map of exactly where to spend the next pass, and that is worth more than a lucky high one would have been.",
  "Most people who go on to clear this checkpoint sat it at least once before they did. The difference was going back in, not getting it right on the first try.",
  "The retake gate is not a punishment - it is a second look at the same week with everything this sitting just told you about where the gaps actually sit.",
  "A result like this is the most specific feedback you will get all week. An evening with the revision deck turns it into the one that does clear.",
  "Forty percent of a hard week is still further than not sitting it at all - and the next attempt starts from here, not from zero.",
  "Nobody remembers the sitting that did not land. They remember the one right after it - the one that did, because of what the first one pointed at.",
];

function _retryQuote(result, attempt) {
  const seed =
    Math.round((result?.score ?? 0) * 1000) +
    (attempt?.attemptNumber || 0) * 7 +
    (attempt?.week || 0);
  return _RETRY_QUOTES[seed % _RETRY_QUOTES.length];
}

function toPercent(score) {
  return Math.round((score ?? 0) * 100);
}

function formatClock(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function WeeklyTestPanel({ profileId, onGraded }) {
  const [phase, setPhase] = useState("board");
  const [board, setBoard] = useState(null);
  const [loadingBoard, setLoadingBoard] = useState(true);
  const [error, setError] = useState(null);

  const [attempt, setAttempt] = useState(null);
  const [question, setQuestion] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(1);
  const [selected, setSelected] = useState(null);
  const [locking, setLocking] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [flagCount, setFlagCount] = useState(0);
  const [warning, setWarning] = useState(null);
  const [result, setResult] = useState(null);
  const [rewardData, setRewardData] = useState(null);

  const pendingEvents = useRef([]);
  const flagThreshold = useRef(5);
  const finishingRef = useRef(false);

  const copyPasteRef = useRef(0);
  const tabSwitchRef = useRef(0);
  const fullscreenBreachedRef = useRef(false);

  const loadBoard = useCallback(async () => {
    setLoadingBoard(true);
    setError(null);
    try {
      const data = await api.get(`/weekly-test/${profileId}/board`);
      setBoard(data);
      flagThreshold.current = data.violation_autosubmit_threshold || 5;
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Could not load this week's checkpoint board just now.",
      );
    } finally {
      setLoadingBoard(false);
    }
  }, [profileId]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  function flag(type) {
    pendingEvents.current = [
      ...pendingEvents.current,
      { type, at: new Date().toISOString() },
    ];
    setFlagCount((prev) => prev + 1);
    setWarning(
      PROCTOR_MESSAGES[type] ||
        "That action was logged on this sitting's proctoring record.",
    );
    if (
      type === "copy_attempt" ||
      type === "paste_attempt" ||
      type === "context_menu" ||
      type === "shortcut_attempt"
    ) {
      copyPasteRef.current += 1;
    } else if (type === "tab_switch") {
      tabSwitchRef.current += 1;
    } else if (type === "fullscreen_exit") {
      fullscreenBreachedRef.current = true;
    }
  }

  useEffect(() => {
    if (phase !== "active") return undefined;

    const blockAndFlag = (type) => (event) => {
      event.preventDefault();
      flag(type);
    };
    const onCopy         = blockAndFlag("copy_attempt");
    const onCut          = blockAndFlag("copy_attempt");
    const onPaste        = blockAndFlag("paste_attempt");
    const onContextMenu  = blockAndFlag("context_menu");
    const onVisibility   = () => { if (document.hidden) flag("tab_switch"); };
    const onFsChange     = () => { if (!document.fullscreenElement) flag("fullscreen_exit"); };
    const onKeyDown      = (event) => {
      const blocked =
        (event.ctrlKey || event.metaKey) &&
        ["c", "x", "v", "u", "p"].includes(event.key.toLowerCase());
      if (blocked || event.key === "F12") {
        event.preventDefault();
        flag("shortcut_attempt");
      }
    };

    document.addEventListener("copy",             onCopy);
    document.addEventListener("cut",              onCut);
    document.addEventListener("paste",            onPaste);
    document.addEventListener("contextmenu",      onContextMenu);
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("fullscreenchange", onFsChange);
    document.addEventListener("keydown",          onKeyDown);

    return () => {
      document.removeEventListener("copy",             onCopy);
      document.removeEventListener("cut",              onCut);
      document.removeEventListener("paste",            onPaste);
      document.removeEventListener("contextmenu",      onContextMenu);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("fullscreenchange", onFsChange);
      document.removeEventListener("keydown",          onKeyDown);
    };
  }, [phase]);

  useEffect(() => {
    if (phase !== "active" || !attempt) return undefined;
    const tick = window.setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          window.clearInterval(tick);
          if (!finishingRef.current) forceFinish("time_expired");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(tick);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, attempt]);

  useEffect(() => {
    if (phase === "active" && flagCount >= flagThreshold.current && !finishingRef.current) {
      forceFinish("proctoring_threshold");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flagCount, phase]);

  function requestProctoredFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
  }

  function exitProctoredFullscreen() {
    if (document.fullscreenElement && document.exitFullscreen)
      document.exitFullscreen().catch(() => {});
  }

  async function startTest(week) {
    setPhase("starting");
    setError(null);
    setWarning(null);
    setFlagCount(0);
    setResult(null);
    setRewardData(null);
    pendingEvents.current = [];
    finishingRef.current = false;
    copyPasteRef.current = 0;
    tabSwitchRef.current = 0;
    fullscreenBreachedRef.current = false;
    try {
      const data = await api.post(`/weekly-test/${profileId}/start`, { week });
      setAttempt({
        id: data.attempt_id,
        week: data.week,
        attemptNumber: data.attempt_number,
        total: data.total_questions,
        passFloor: data.pass_floor,
        partialFloor: data.partial_floor,
        timeLimitMinutes: data.time_limit_minutes,
      });
      setQuestion(data.first_question);
      setQuestionIndex(data.question_index);
      setSelected(null);
      setSecondsLeft(data.seconds_remaining ?? data.time_limit_minutes * 60);
      if (data.resumed) {
        setWarning(
          "Picking up where that sitting left off - the clock kept running while it sat open.",
        );
      }
      setPhase("active");
      requestProctoredFullscreen();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Could not open this checkpoint right now - try again shortly.",
      );
      setPhase("board");
    }
  }

  async function lockInAnswer() {
    if (selected === null || !attempt || !question) return;
    setLocking(true);
    setError(null);
    const events = pendingEvents.current;
    pendingEvents.current = [];
    try {
      const data = await api.post(`/weekly-test/${profileId}/answer`, {
        attempt_id: attempt.id,
        question_id: question.id,
        choice: selected,
        proctor_events: events,
      });
      if (data.finished) {
        finishingRef.current = true;
        finalizeResult(data);
      } else {
        setQuestion(data.next_question);
        setQuestionIndex(data.question_index + 1);
        setSelected(null);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "That answer did not lock in - try once more.",
      );
    } finally {
      setLocking(false);
    }
  }

  async function forceFinish(reason) {
    if (!attempt || !question || finishingRef.current) return;
    finishingRef.current = true;
    setLocking(true);
    const events = [
      ...pendingEvents.current,
      { type: reason, at: new Date().toISOString() },
    ];
    pendingEvents.current = [];
    try {
      const data = await api.post(`/weekly-test/${profileId}/answer`, {
        attempt_id: attempt.id,
        question_id: question.id,
        choice: selected || "",
        proctor_events: events,
      });
      finalizeResult(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "This sitting ended, but the result did not come back cleanly - reload the board to check it.",
      );
      setPhase("board");
      loadBoard();
    } finally {
      setLocking(false);
    }
  }

  function finalizeResult(data) {
    exitProctoredFullscreen();
    setResult(data);
    setPhase("finished");
    const scorePercent = Math.round((data.score || 0) * 100);
    if (scorePercent >= 50) {
      setRewardData({
        finalScore: scorePercent,
        proctoringLog: {
          copyPasteAttempts: copyPasteRef.current,
          tabSwitches: tabSwitchRef.current,
          fullscreenBreached: fullscreenBreachedRef.current,
        },
      });
    }
    loadBoard();
    onGraded?.();
  }

  function backToBoard() {
    setPhase("board");
    setAttempt(null);
    setQuestion(null);
    setResult(null);
    setRewardData(null);
    setWarning(null);
    loadBoard();
  }

  const weeks = board?.weeks || [];

  return (
    <BentoCard className="flex flex-col gap-6">
      {rewardData ? (
        <GamificationReward
          active={Boolean(rewardData)}
          assessmentType="CHECKPOINT"
          finalScore={rewardData.finalScore}
          proctoringLog={rewardData.proctoringLog}
          onDone={() => setRewardData(null)}
        />
      ) : null}

      <div>
        <Eyebrow>Weekly checkpoint</Eyebrow>
        <h3 className="mt-2 font-display text-xl font-semibold text-cap-navy">
          Proctored test, one week at a time
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-cap-slate">
          Each week's test stays locked until that week's modules are marked
          done, runs on a visible clock with copy, paste and tab-switching
          watched and logged, and asks every question once, in order, with
          nothing to skip. Forty percent or below does not clear it, forty to
          seventy-nine reads as partially there, and eighty and over opens the
          next week.
        </p>
      </div>

      {error ? (
        <div className="rounded-2xl border border-signal-bad/30 bg-signal-bad/5 px-4 py-3 text-sm text-signal-bad">
          {error}
        </div>
      ) : null}

      {phase === "board" ? (
        <BoardView weeks={weeks} loading={loadingBoard} onStart={startTest} />
      ) : null}

      {phase === "starting" ? (
        <div className="flex items-center justify-center gap-2 rounded-2xl border border-cap-line bg-cap-mist/40 px-4 py-10 text-sm text-cap-slate">
          <Loader2 className="h-4 w-4 animate-spin" /> Building this week's
          paper - fresh questions, every sitting.
        </div>
      ) : null}

      {phase === "active" && attempt && question ? (
        <ActiveSitting
          attempt={attempt}
          question={question}
          questionIndex={questionIndex}
          secondsLeft={secondsLeft}
          selected={selected}
          onSelect={setSelected}
          onLockIn={lockInAnswer}
          locking={locking}
          flagCount={flagCount}
          flagThreshold={flagThreshold.current}
          warning={warning}
          onDismissWarning={() => setWarning(null)}
        />
      ) : null}

      {phase === "finished" && result ? (
        <ResultView attempt={attempt} result={result} onBack={backToBoard} />
      ) : null}
    </BentoCard>
  );
}

const PROCTOR_MESSAGES = {
  copy_attempt:
    "Copying from this page is blocked during a sitting - that attempt has been logged.",
  paste_attempt:
    "Pasting into an answer is blocked during a sitting - that attempt has been logged.",
  context_menu: "The right-click menu stays off during a sitting - logged.",
  tab_switch:
    "Leaving this tab was caught and logged - the clock kept running.",
  fullscreen_exit:
    "Leaving full screen was caught and logged - staying in full screen keeps the count down.",
  shortcut_attempt:
    "That keyboard shortcut is blocked during a sitting - logged.",
};

function BoardView({ weeks, loading, onStart }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 rounded-2xl border border-cap-line bg-cap-mist/40 px-4 py-10 text-sm text-cap-slate">
        <Loader2 className="h-4 w-4 animate-spin" /> Reading this plan's
        week-by-week status.
      </div>
    );
  }
  if (!weeks.length) {
    return (
      <p className="rounded-2xl border border-cap-line bg-cap-mist/40 px-4 py-6 text-sm text-cap-slate">
        Once a roadmap is active, its weeks will line up here, each one gated
        behind its own modules.
      </p>
    );
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {weeks.map((week) => {
        const copy = LOCK_COPY[week.lock_state] || LOCK_COPY.locked;
        const Icon = copy.icon;
        const startable =
          week.lock_state === "ready" || week.lock_state === "retake_ready";
        return (
          <div
            key={week.week}
            className="flex flex-col gap-3 rounded-2xl border border-cap-line bg-white p-4"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="font-display text-sm font-semibold text-cap-navy">
                Week {week.week} checkpoint
              </p>
              <StatusPill status={copy.tone}>
                <Icon className="h-3.5 w-3.5" /> {copy.label}
              </StatusPill>
            </div>
            <p className="text-xs leading-relaxed text-cap-slate">
              {week.reason}
            </p>
            {week.last_score !== null && week.last_score !== undefined ? (
              <p className="text-xs text-cap-slate">
                Last sitting:{" "}
                <span className="font-semibold text-cap-navy">
                  {toPercent(week.last_score)} percent
                </span>
                {week.best_band ? (
                  <>
                    {" - "}
                    {(BAND_COPY[week.best_band] || {}).label || week.best_band}
                  </>
                ) : null}
                {week.attempt_count > 1 ? (
                  <> across {week.attempt_count} attempts</>
                ) : null}
              </p>
            ) : null}
            <Button
              variant={startable ? "primary" : "secondary"}
              className={cx(!startable && "cursor-not-allowed opacity-60")}
              disabled={!startable}
              onClick={() => startable && onStart(week.week)}
            >
              {week.lock_state === "retake_ready"
                ? "Retake checkpoint"
                : "Start checkpoint"}{" "}
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function QuestionMetaStrip({ question }) {
  const typeMeta = question.question_type ? Q_TYPE_META[question.question_type] : null;
  const diffCls  = question.difficulty    ? DIFF_CLS[question.difficulty]       : null;

  if (!typeMeta && !diffCls && !question.concept_tag) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {typeMeta ? (
        <span
          className={cx(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
            typeMeta.cls,
          )}
        >
          <typeMeta.Icon className="h-3 w-3" />
          {typeMeta.label}
        </span>
      ) : null}

      {diffCls ? (
        <span
          className={cx(
            "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
            diffCls,
          )}
        >
          {question.difficulty}
        </span>
      ) : null}

      {question.time_limit_seconds ? (
        <span className="inline-flex items-center gap-1 text-xs text-cap-slate">
          <Clock className="h-3 w-3" />
          {question.time_limit_seconds}s suggested
        </span>
      ) : null}

      {question.concept_tag ? (
        <span className="max-w-xs truncate text-xs text-cap-slate">
          {question.concept_tag}
        </span>
      ) : null}
    </div>
  );
}

function ActiveSitting({
  attempt,
  question,
  questionIndex,
  secondsLeft,
  selected,
  onSelect,
  onLockIn,
  locking,
  flagCount,
  flagThreshold,
  warning,
  onDismissWarning,
}) {
  const lowOnTime  = secondsLeft <= 60;
  const total      = attempt.total || 1;
  const progressPct = Math.min(100, Math.round(((questionIndex - 1) / total) * 100));

  return (
    <div
      className="flex flex-col gap-4 rounded-2xl border border-cap-navy/30 bg-white p-5"
      style={{ userSelect: "none" }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cap-line pb-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cap-vibrant">
          <Maximize className="h-3.5 w-3.5" /> Week {attempt.week} checkpoint
          - question {questionIndex} of {attempt.total}
        </div>
        <div className="flex items-center gap-3">
          <span
            className={cx(
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold",
              lowOnTime
                ? "border-signal-bad/40 bg-signal-bad/10 text-signal-bad"
                : "border-cap-line bg-cap-mist/60 text-cap-navy",
            )}
          >
            <Clock className="h-4 w-4" /> {formatClock(secondsLeft)}
          </span>
          <span
            className={cx(
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium",
              flagCount > 0
                ? "border-signal-warn/40 bg-signal-warn/10 text-signal-warn"
                : "border-cap-line text-cap-slate",
            )}
          >
            <ShieldAlert className="h-3.5 w-3.5" /> {flagCount}/{flagThreshold}{" "}
            flags
          </span>
        </div>
      </div>

      <div className="h-1 w-full overflow-hidden rounded-full bg-cap-line">
        <div
          className="h-full rounded-full bg-cap-blue transition-all duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {warning ? (
        <div className="flex items-start gap-2 rounded-xl border border-signal-warn/30 bg-signal-warn/10 px-3 py-2 text-xs text-signal-warn">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p className="flex-1">{warning}</p>
          <button
            type="button"
            onClick={onDismissWarning}
            aria-label="Dismiss"
            className="rounded-full p-0.5 hover:bg-white/40"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : null}

      <QuestionMetaStrip question={question} />

      <p className="font-display text-base font-semibold leading-relaxed text-cap-navy">
        {question.prompt}
      </p>

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
                isChosen
                  ? "border-cap-blue bg-cap-blue/5 text-cap-navy"
                  : "border-cap-line text-cap-slate hover:border-cap-blue/50 hover:bg-cap-mist/50",
              )}
            >
              {isChosen ? (
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cap-blue" />
              ) : (
                <Circle className="mt-0.5 h-4 w-4 shrink-0 text-cap-line" />
              )}
              <span>{option}</span>
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-cap-line pt-3">
        <p className="text-xs text-cap-slate">
          No going back to a question once it is locked in - that is what keeps
          a sitting honest.
        </p>
        <Button onClick={onLockIn} disabled={selected === null || locking}>
          {locking ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Lock in this answer <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function ScoredEntry({ entry, index }) {
  const [expanded, setExpanded] = useState(false);

  const typeMeta = entry.question_type ? Q_TYPE_META[entry.question_type] : null;
  const diffCls  = entry.difficulty    ? DIFF_CLS[entry.difficulty]       : null;

  const { whyChosenWrong, whyCorrect } = useMemo(() => {
    if (entry.is_correct || !entry.justification) {
      return { whyChosenWrong: null, whyCorrect: entry.justification?.whyCorrect || null };
    }
    const opts = entry.options || [];
    const idx  = opts.indexOf(entry.chosen);
    const letter = idx >= 0 ? ["A", "B", "C", "D"][idx] : null;
    return {
      whyChosenWrong: letter ? (entry.justification[`why${letter}IsWrong`] || null) : null,
      whyCorrect:     entry.justification.whyCorrect || null,
    };
  }, [entry]);

  const hasExplanation = !entry.is_correct && (whyCorrect || whyChosenWrong);

  return (
    <div
      className={cx(
        "rounded-xl border px-4 py-3 text-sm leading-relaxed",
        entry.is_correct
          ? "border-signal-good/30 bg-signal-good/5"
          : "border-signal-bad/25 bg-signal-bad/5",
      )}
    >
      <div className="flex items-start gap-2">
        {entry.is_correct ? (
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-signal-good" />
        ) : (
          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-signal-bad" />
        )}
        <div className="min-w-0 flex-1">
          {(typeMeta || diffCls || entry.concept_tag) ? (
            <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
              {typeMeta ? (
                <span
                  className={cx(
                    "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
                    typeMeta.cls,
                  )}
                >
                  <typeMeta.Icon className="h-3 w-3" />
                  {typeMeta.label}
                </span>
              ) : null}
              {diffCls ? (
                <span
                  className={cx(
                    "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                    diffCls,
                  )}
                >
                  {entry.difficulty}
                </span>
              ) : null}
              {entry.concept_tag ? (
                <span className="text-xs text-cap-slate">{entry.concept_tag}</span>
              ) : null}
            </div>
          ) : null}

          <p className="font-medium text-cap-navy">
            Q{index + 1}. {entry.prompt}
          </p>

          <p className="mt-1 text-xs text-cap-slate">
            Your answer:{" "}
            <span className="font-medium text-cap-ink">
              {entry.chosen || "left blank"}
            </span>
            {!entry.is_correct ? (
              <>
                {" - "}correct answer:{" "}
                <span className="font-medium text-cap-ink">
                  {entry.correct_option}
                </span>
              </>
            ) : null}
          </p>

          {entry.explainer ? (
            <p className="mt-1 text-xs text-cap-slate">{entry.explainer}</p>
          ) : null}

          {hasExplanation ? (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="inline-flex items-center gap-1 text-xs font-medium text-cap-blue hover:underline"
              >
                {expanded ? (
                  <><ChevronUp className="h-3 w-3" /> Hide explanation</>
                ) : (
                  <><ChevronDown className="h-3 w-3" /> Why was this wrong?</>
                )}
              </button>

              {expanded ? (
                <div className="mt-2 flex flex-col gap-2 rounded-xl border border-cap-line bg-white/80 px-3 py-2.5">
                  {whyCorrect ? (
                    <div>
                      <p className="text-xs font-semibold text-signal-good">
                        Why the correct answer is right
                      </p>
                      <p className="mt-0.5 text-xs text-cap-slate">{whyCorrect}</p>
                    </div>
                  ) : null}
                  {whyChosenWrong ? (
                    <div>
                      <p className="text-xs font-semibold text-signal-bad">
                        Why your choice was incorrect
                      </p>
                      <p className="mt-0.5 text-xs text-cap-slate">{whyChosenWrong}</p>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ConceptReviewStrip({ concepts, passing }) {
  if (!concepts || concepts.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <Eyebrow>
        {passing ? "Concepts to revisit" : "Concepts that need work"}
      </Eyebrow>
      <p className="text-xs text-cap-slate">
        {passing
          ? "You cleared the bar - but these topics had incorrect answers. A quick pass over the revision deck keeps them solid."
          : "These topics had the most impact on this sitting's score - a focused read through the revision deck before the retake is what changes the next result."}
      </p>
      <div className="flex flex-col gap-1.5">
        {concepts.map((c) => {
          const typeMeta = c.questionType ? Q_TYPE_META[c.questionType] : null;
          const diffCls  = c.difficulty   ? DIFF_CLS[c.difficulty]      : null;
          return (
            <div
              key={c.questionId}
              className="flex items-start gap-2 rounded-xl border border-cap-line bg-white px-3 py-2"
            >
              <AlertTriangle
                className={cx(
                  "mt-0.5 h-3.5 w-3.5 shrink-0",
                  passing ? "text-signal-warn" : "text-signal-bad",
                )}
              />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs font-medium text-cap-navy">
                    {c.conceptTag}
                  </span>
                  {typeMeta ? (
                    <span
                      className={cx(
                        "inline-flex items-center gap-1 rounded-full border px-1.5 py-px text-xs",
                        typeMeta.cls,
                      )}
                    >
                      <typeMeta.Icon className="h-2.5 w-2.5" />
                      {typeMeta.label}
                    </span>
                  ) : null}
                  {diffCls ? (
                    <span
                      className={cx(
                        "inline-flex items-center rounded-full border px-1.5 py-px text-xs",
                        diffCls,
                      )}
                    >
                      {c.difficulty}
                    </span>
                  ) : null}
                </div>
                <p className="mt-0.5 text-xs text-cap-slate">
                  {c.recommendedReview}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ResultView({ attempt, result, onBack }) {
  const band = BAND_COPY[result.band] || BAND_COPY.failed;

  const scorePercent    = toPercent(result.score);
  const aboveCelebFloor = result.celebration_trigger ?? (scorePercent >= 50);
  const conceptsToShow  = aboveCelebFloor
    ? (result.weak_concepts_detected  || [])
    : (result.failed_concepts         || []);

  return (
    <div className="flex flex-col gap-5">
      <div
        className={cx(
          "flex flex-col items-start gap-3 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between",
          result.band === "passed"
            ? "border-signal-good/30 bg-signal-good/5"
            : result.band === "partial"
            ? "border-signal-warn/30 bg-signal-warn/5"
            : "border-signal-bad/30 bg-signal-bad/5",
        )}
      >
        <div>
          <StatusPill status={band.tone}>
            {result.band === "passed" ? (
              <Trophy className="h-3.5 w-3.5" />
            ) : (
              <ShieldAlert className="h-3.5 w-3.5" />
            )}{" "}
            {band.label}
          </StatusPill>
          <p className="mt-2 font-display text-lg font-semibold text-cap-navy">
            {scorePercent} percent overall
            {result.auto_submitted ? " - sitting ended early" : ""}
          </p>
          <p className="mt-1 text-sm leading-relaxed text-cap-slate">
            {result.feedback}
          </p>
          {result.next_module_unlocked ? (
            <p className="mt-1.5 text-xs font-medium text-signal-good">
              Next module unlocked
            </p>
          ) : null}
        </div>
        <Button variant="secondary" onClick={onBack}>
          Back to the checkpoint board
        </Button>
      </div>

      {result.band !== "passed" ? (
        <div className="flex items-start gap-3 rounded-2xl border border-cap-line bg-cap-mist/40 px-4 py-3.5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cap-blue/10 text-cap-blue">
            <BookOpen className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="text-sm leading-relaxed text-cap-ink">
              {_retryQuote(result, attempt)}
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-cap-slate">
              Worth a real pass through this week's revision deck before the
              retake opens back up - that is exactly what the gate ahead is
              built to reward, not just to require.
            </p>
          </div>
        </div>
      ) : null}

      <ConceptReviewStrip concepts={conceptsToShow} passing={aboveCelebFloor} />

      <div className="flex flex-col gap-2">
        <Eyebrow>Where each answer landed</Eyebrow>
        {(result.scored_questions || []).map((entry, index) => (
          <ScoredEntry key={entry.question_id} entry={entry} index={index} />
        ))}
      </div>
    </div>
  );
}
