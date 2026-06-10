"use client";

import { useEffect, useRef, useState } from "react";
import { Sparkles, Send, ChevronRight, Loader2, Star, ShieldCheck, ShieldAlert, RotateCcw, X, CheckCircle2, XCircle, Circle } from "lucide-react";
import { BentoCard, Eyebrow, Button, StatusPill } from "@/components/ui";
import { GamificationReward } from "@/components/GamificationReward";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/cx";

const COMPANIES = [
  { value: "cap_exceller", label: "Capgemini Exceller" },
  { value: "tcs_nqt", label: "TCS NQT" },
  { value: "infytq", label: "Infosys InfyTQ" },
  { value: "wipro_nlth", label: "Wipro NLTH" },
  { value: "accenture_asset", label: "Accenture ASSET" },
  { value: "cognizant_genc", label: "Cognizant GenC" },
];

const CURATED_DRIVES = new Set(["cap_exceller"]);

const ROUND_TYPES = [
  { value: "technical", label: "Technical", note: "Questions drawn from your own gap map and the role's critical path" },
  { value: "aptitude", label: "Aptitude", note: "Numerical, verbal and logical reasoning, the way the screening test runs it" },
  { value: "behavioral", label: "Behavioural", note: "Situation, action, result - the questions a panel actually circles back to" },
  { value: "hr", label: "HR", note: "The closing-round questions about fit, direction and follow-through" },
];

function toTen(score) {
  return Math.round(score * 10 * 10) / 10;
}

const PROCTOR_MESSAGES = {
  copy_attempt: "Copying from this page is blocked during a round - that attempt has been logged.",
  paste_attempt: "Pasting into an answer is blocked during a round - an interview rewards your own words, not a pasted one.",
  context_menu: "The right-click menu stays off during a round - logged.",
  tab_switch: "Leaving this tab was caught and logged - a real panel would have noticed too.",
  fullscreen_exit: "Leaving full screen was caught and logged - staying in full screen keeps the count down.",
  shortcut_attempt: "That keyboard shortcut is blocked during a round - logged.",
};

export function InterviewPanel({ profileId, targetRole }) {
  const [phase, setPhase] = useState("setup");
  const [company, setCompany] = useState(COMPANIES[0].value);
  const [roundType, setRoundType] = useState(ROUND_TYPES[0].value);
  const [error, setError] = useState(null);

  const [sessionId, setSessionId] = useState(null);
  const [roundLabel, setRoundLabel] = useState("");
  const [companyDisplay, setCompanyDisplay] = useState("");
  const [fairnessNote, setFairnessNote] = useState(null);
  const [isDriveCurated, setIsDriveCurated] = useState(false);
  const [totalSeconds, setTotalSeconds] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [grading, setGrading] = useState(false);
  const [scored, setScored] = useState(null);
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [postReport, setPostReport] = useState(null);

  const [reward, setReward] = useState(null);

  const [flagCount, setFlagCount] = useState(0);
  const [warning, setWarning] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const timerRef = useRef(null);

  const copyPasteRef = useRef(0);
  const tabSwitchRef = useRef(0);
  const fullscreenBreachedRef = useRef(false);

  function flag(type) {
    setFlagCount((prev) => prev + 1);
    setWarning(PROCTOR_MESSAGES[type] || "That action was caught and logged for this round.");
    if (type === "copy_attempt" || type === "paste_attempt" || type === "context_menu" || type === "shortcut_attempt") {
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
    const onCopy = blockAndFlag("copy_attempt");
    const onCut = blockAndFlag("copy_attempt");
    const onPaste = blockAndFlag("paste_attempt");
    const onContextMenu = blockAndFlag("context_menu");
    const onVisibility = () => {
      if (document.hidden) flag("tab_switch");
    };
    const onFullscreenChange = () => {
      if (!document.fullscreenElement) flag("fullscreen_exit");
    };
    const onKeyDown = (event) => {
      const blockedCombo = (event.ctrlKey || event.metaKey) && ["c", "x", "v", "u", "p"].includes(event.key.toLowerCase());
      if (blockedCombo || event.key === "F12") {
        event.preventDefault();
        flag("shortcut_attempt");
      }
    };

    document.addEventListener("copy", onCopy);
    document.addEventListener("cut", onCut);
    document.addEventListener("paste", onPaste);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("copy", onCopy);
      document.removeEventListener("cut", onCut);
      document.removeEventListener("paste", onPaste);
      document.removeEventListener("contextmenu", onContextMenu);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("fullscreenchange", onFullscreenChange);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [phase]);

  useEffect(() => {
    if (phase !== "active" || scored !== null) {
      clearInterval(timerRef.current);
      return;
    }
    const question = questions[index];
    if (!question) return;
    const limit = question.time_limit || 90;
    setTimeLeft(limit);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          setAnswer((currentAnswer) => {
            if (currentAnswer.trim()) {
              setTimeout(() => {
                document.getElementById("interview-submit-btn")?.click();
              }, 0);
            } else {
              const timedEntry = {
                question,
                answer: "",
                overall_score: 0,
                rubric_dimensions: [],
                feedback: "Time ran out before an answer was submitted - marked as zero for this question.",
                correct_option: question.answer || null,
                justification: question.justification || null,
              };
              setHistory((prev) => [...prev, timedEntry]);
              setScored(timedEntry);
            }
            return currentAnswer;
          });
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, index, scored, questions]);

  function requestProctoredFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen().catch(() => {});
    }
  }

  function exitProctoredFullscreen() {
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    }
  }

  async function start() {
    setPhase("starting");
    setError(null);
    setFlagCount(0);
    setWarning(null);
    setReward(null);
    copyPasteRef.current = 0;
    tabSwitchRef.current = 0;
    fullscreenBreachedRef.current = false;
    try {
      const result = await api.post(`/interview/${profileId}/start`, { company, round_type: roundType });
      setSessionId(result.session_id);
      setRoundLabel(result.round_label);
      setCompanyDisplay(result.company_display);
      setFairnessNote(result.fairness_note);
      setIsDriveCurated(result.is_drive_curated || false);
      setTotalSeconds(result.total_time_seconds || null);
      setQuestions(result.questions);
      setIndex(0);
      setAnswer("");
      setScored(null);
      setHistory([]);
      setSummary(null);
      setPostReport(null);
      setPhase("active");
      requestProctoredFullscreen();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not start a round just now - try again in a moment.");
      setPhase("setup");
    }
  }

  async function submitAnswer() {
    if (!answer.trim()) return;
    setGrading(true);
    setError(null);
    const question = questions[index];
    try {
      const result = await api.post(`/interview/${profileId}/answer`, {
        session_id: sessionId,
        question_id: question.id,
        answer: answer.trim(),
      });
      setScored(result);
      setHistory((prev) => [...prev, { question, answer: answer.trim(), ...result }]);
      if (result.session_complete) {
        setSummary(result.session_summary);
        if (result.post_interview_report) {
          setPostReport(result.post_interview_report);
          const scorePercent = result.post_interview_report.raw_score_pct ?? 0;
          if (scorePercent >= 60) {
            setReward({
              finalScore: scorePercent,
              proctoringLog: {
                copyPasteAttempts: copyPasteRef.current,
                tabSwitches: tabSwitchRef.current,
                fullscreenBreached: fullscreenBreachedRef.current,
              },
            });
          }
        }
        exitProctoredFullscreen();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "That answer did not get graded - try sending it again.");
    } finally {
      setGrading(false);
    }
  }

  function nextQuestion() {
    clearInterval(timerRef.current);
    setTimeLeft(null);
    setIndex((prev) => prev + 1);
    setAnswer("");
    setScored(null);
  }

  function restart() {
    clearInterval(timerRef.current);
    setTimeLeft(null);
    exitProctoredFullscreen();
    setPhase("setup");
    setSessionId(null);
    setQuestions([]);
    setHistory([]);
    setSummary(null);
    setPostReport(null);
    setScored(null);
    setReward(null);
    setFlagCount(0);
    setWarning(null);
    copyPasteRef.current = 0;
    tabSwitchRef.current = 0;
    fullscreenBreachedRef.current = false;
  }

  if (phase === "setup" || phase === "starting") {
    return (
      <div className="space-y-6">
        <BentoCard>
          <Eyebrow>Mock interviewer</Eyebrow>
          <h3 className="mt-1 font-display text-lg font-semibold text-cap-navy">Run a round shaped to a real placement drive</h3>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-cap-slate">
            Pick the drive and the round type, and the agent builds a short set of
            questions from {targetRole ? <span className="font-medium text-cap-ink">{targetRole}</span> : "your target role"}
            's critical path and your own gap map where one exists. Each answer is graded
            on the spot, dimension by dimension, against the same rubric a real panel
            for that round would lean on.
          </p>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <Eyebrow>Drive</Eyebrow>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {COMPANIES.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setCompany(item.value)}
                    className={cx(
                      "rounded-xl border px-3 py-2.5 text-left text-sm font-medium transition-colors",
                      company === item.value
                        ? "border-cap-blue bg-cap-mist text-cap-navy"
                        : "border-cap-line bg-white text-cap-slate hover:border-cap-blue/40",
                    )}
                  >
                    <span className="block">{item.label}</span>
                    {CURATED_DRIVES.has(item.value) ? (
                      <span className="mt-1 inline-flex items-center gap-1 rounded-full border border-cap-blue/30 bg-white px-2 py-0.5 text-[10px] font-medium text-cap-blue">
                        <ShieldCheck className="h-2.5 w-2.5" /> Drive-calibrated
                      </span>
                    ) : null}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Eyebrow>Round</Eyebrow>
              <div className="mt-2 space-y-2">
                {ROUND_TYPES.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setRoundType(item.value)}
                    className={cx(
                      "block w-full rounded-xl border px-3 py-2.5 text-left transition-colors",
                      roundType === item.value
                        ? "border-cap-blue bg-cap-mist"
                        : "border-cap-line bg-white hover:border-cap-blue/40",
                    )}
                  >
                    <span className="text-sm font-medium text-cap-navy">{item.label}</span>
                    <span className="mt-0.5 block text-xs leading-relaxed text-cap-slate">{item.note}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {error ? <p className="mt-4 text-sm text-signal-bad">{error}</p> : null}

          <Button onClick={start} variant="primary" className="mt-6" disabled={phase === "starting"}>
            {phase === "starting" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {phase === "starting" ? "Building your round..." : "Start the round"}
          </Button>
        </BentoCard>
      </div>
    );
  }

  const question = questions[index];
  const isLast = index === questions.length - 1;
  const allDone = Boolean(summary);

  return (
    <div className="space-y-6">
      {reward ? (
        <GamificationReward
          active={Boolean(reward)}
          assessmentType="MOCK_INTERVIEW"
          finalScore={reward.finalScore}
          proctoringLog={reward.proctoringLog}
          onDone={() => setReward(null)}
        />
      ) : null}

      <BentoCard className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Eyebrow>{companyDisplay} · {roundLabel}</Eyebrow>
            {isDriveCurated ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-cap-blue/30 bg-cap-mist px-2 py-0.5 text-[11px] font-medium text-cap-blue">
                <ShieldCheck className="h-3 w-3" /> Drive-calibrated
              </span>
            ) : null}
          </div>
          <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
            {allDone ? "Round complete" : `Question ${index + 1} of ${questions.length}`}
          </h3>
          {totalSeconds && !allDone ? (
            <p className="mt-0.5 text-xs text-cap-slate">
              {Math.floor(totalSeconds / 60)} min total · each question has its own timer shown below
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          {!allDone ? (
            <span className={cx(
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium",
              flagCount > 0 ? "border-signal-warn/40 bg-signal-warn/10 text-signal-warn" : "border-cap-line text-cap-slate",
            )}>
              <ShieldAlert className="h-3.5 w-3.5" /> {flagCount} flag{flagCount === 1 ? "" : "s"} this round
            </span>
          ) : null}
          <Button variant="ghost" onClick={restart}>
            <RotateCcw className="h-4 w-4" />
            Run a different round
          </Button>
        </div>
      </BentoCard>

      {!allDone ? (
        <p className="-mt-3 px-1 text-xs leading-relaxed text-cap-slate">
          This round runs under the same watch as a proctored checkpoint - copying, pasting, the right-click
          menu and dev-tool shortcuts stay off, and leaving full screen or this tab gets caught and counted.
          Nothing here ends the round early; it just keeps the conditions honest, the way the real thing would.
        </p>
      ) : null}

      {warning ? (
        <div className="flex items-start gap-2 rounded-xl border border-signal-warn/30 bg-signal-warn/10 px-3 py-2 text-xs text-signal-warn">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p className="flex-1">{warning}</p>
          <button type="button" onClick={() => setWarning(null)} aria-label="Dismiss" className="rounded-full p-0.5 hover:bg-white/40">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : null}

      {fairnessNote ? (
        <BentoCard className="border-cap-line bg-cap-mist/40">
          <p className="flex items-start gap-2 text-xs leading-relaxed text-cap-slate">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cap-blue" />
            {fairnessNote}
          </p>
        </BentoCard>
      ) : null}

      {!allDone && question ? (
        <BentoCard>
          <div className="flex flex-wrap items-center gap-2">
            {question.section ? (
              <span className="rounded-full border border-cap-line bg-white px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-cap-blue">
                {question.section}
              </span>
            ) : (
              <span className="rounded-full border border-cap-line bg-white px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-cap-slate">
                {question.kind}
              </span>
            )}
            {question.difficulty && question.difficulty !== "Open-Ended" ? (
              <span className={cx(
                "rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
                question.difficulty === "Easy" && "border-signal-good/40 bg-signal-good/10 text-signal-good",
                question.difficulty === "Medium" && "border-signal-warn/40 bg-signal-warn/10 text-signal-warn",
                question.difficulty === "Hard" && "border-signal-bad/40 bg-signal-bad/10 text-signal-bad",
              )}>
                {question.difficulty}
              </span>
            ) : null}
            {question.time_limit ? (
              <span className="text-[11px] text-cap-slate">{question.time_limit}s</span>
            ) : null}
          </div>

          <p className="mt-3 select-none text-base leading-relaxed text-cap-ink">{question.prompt}</p>

          {question.code_snippet ? (
            <pre className="mt-3 select-none overflow-x-auto rounded-xl border border-cap-line bg-cap-navy/5 px-4 py-3 text-[13px] leading-relaxed text-cap-navy">
              <code>{question.code_snippet}</code>
            </pre>
          ) : null}

          {!scored && timeLeft !== null ? (
            <div className="mt-3 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-cap-mist">
                <div
                  className={cx(
                    "h-full rounded-full transition-all duration-1000",
                    timeLeft > (question.time_limit || 90) * 0.5 ? "bg-signal-good" :
                    timeLeft > (question.time_limit || 90) * 0.25 ? "bg-signal-warn" : "bg-signal-bad",
                  )}
                  style={{ width: `${(timeLeft / (question.time_limit || 90)) * 100}%` }}
                />
              </div>
              <span className={cx(
                "w-10 text-right text-xs font-semibold tabular-nums",
                timeLeft > (question.time_limit || 90) * 0.5 ? "text-signal-good" :
                timeLeft > (question.time_limit || 90) * 0.25 ? "text-signal-warn" : "text-signal-bad",
              )}>
                {timeLeft}s
              </span>
            </div>
          ) : null}

          {!scored ? (
            <div className="mt-4">
              {question.options ? (
                <div className="space-y-2">
                  {(Array.isArray(question.options)
                    ? question.options.map((text, i) => ({ key: String.fromCharCode(65 + i), text }))
                    : Object.entries(question.options).map(([key, text]) => ({ key, text }))
                  ).map(({ key, text }) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setAnswer(key)}
                      className={cx(
                        "flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left text-sm transition-colors",
                        answer === key
                          ? "border-cap-blue bg-cap-mist text-cap-navy"
                          : "border-cap-line bg-white text-cap-ink hover:border-cap-blue/40",
                      )}
                    >
                      {answer === key ? (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cap-blue" />
                      ) : (
                        <Circle className="mt-0.5 h-4 w-4 shrink-0 text-cap-line" />
                      )}
                      <span className="mr-1 font-semibold">{key}.</span>
                      {text}
                    </button>
                  ))}
                </div>
              ) : (
                <textarea
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  rows={5}
                  placeholder="Answer the way you would out loud - the rubric reads for substance, not polish."
                  className="w-full rounded-xl border border-cap-line bg-white px-4 py-3 text-sm text-cap-ink placeholder:text-cap-slate/70 focus:border-cap-blue focus:outline-none focus:ring-2 focus:ring-cap-blue/20"
                />
              )}
              <div className="mt-3 flex items-center justify-between">
                <span className="text-xs text-cap-slate">
                  {question.options
                    ? answer
                      ? `Option ${answer} selected`
                      : "Pick the option you would actually go with"
                    : `${answer.trim().split(/\s+/).filter(Boolean).length} words`}
                </span>
                <Button id="interview-submit-btn" onClick={submitAnswer} variant="primary" disabled={grading || !answer.trim()}>
                  {grading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {grading ? "Grading..." : question.options ? "Lock in this answer" : "Submit answer"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <ScoreCard scored={scored} question={question} chosen={history[history.length - 1]?.answer} />
              <div className="flex justify-end">
                {isLast ? (
                  <span className="text-sm font-medium text-cap-slate">That was the last question - the summary is below.</span>
                ) : (
                  <Button onClick={nextQuestion} variant="primary">
                    Next question
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
        </BentoCard>
      ) : null}

      {allDone ? (
        <BentoCard className="bg-cap-mist/50">
          <Eyebrow>Round summary</Eyebrow>
          <p className="mt-2 text-sm leading-relaxed text-cap-ink">{summary}</p>
        </BentoCard>
      ) : null}

      {allDone && postReport ? <PostInterviewReport report={postReport} /> : null}

      {history.length > 0 ? (
        <BentoCard>
          <Eyebrow>Every answer this round, scored</Eyebrow>
          <div className="mt-3 space-y-3">
            {history.map((entry, idx) => (
              <div key={entry.question.id} className="rounded-xl border border-cap-line bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-cap-ink">Q{idx + 1}. {entry.question.prompt}</p>
                  <ScorePill score={entry.overall_score} />
                </div>
                <p className="mt-2 text-xs leading-relaxed text-cap-slate">{entry.feedback}</p>
              </div>
            ))}
          </div>
        </BentoCard>
      ) : null}

      {error ? <p className="text-sm text-signal-bad">{error}</p> : null}
    </div>
  );
}

function ScorePill({ score }) {
  const ten = toTen(score);
  const status = ten >= 8 ? "good" : ten >= 5 ? "warn" : "bad";
  return (
    <StatusPill status={status}>
      <Star className="h-3 w-3" />
      {ten.toFixed(1)} / 10
    </StatusPill>
  );
}

function ScoreCard({ scored, question, chosen }) {
  const ten = toTen(scored.overall_score);
  const isMcq = Boolean(question?.options);

  return (
    <div className="rounded-xl border border-cap-line bg-cap-mist/40 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-cap-navy">
          {isMcq ? (ten >= 8 ? "Correct" : "Not quite") : `Scored ${ten.toFixed(1)} / 10`}
        </span>
        <ScorePill score={scored.overall_score} />
      </div>

      {isMcq ? (
        <div className="mt-3 space-y-1.5">
          {(Array.isArray(question.options)
            ? question.options.map((text, i) => ({ key: String.fromCharCode(65 + i), text }))
            : Object.entries(question.options).map(([key, text]) => ({ key, text }))
          ).map(({ key, text }) => {
            const wasChosen = key === chosen;
            const isKeyed = key === scored.correct_option || text === scored.correct_option;
            const justification = scored.justification;
            const justNote = justification
              ? key === scored.correct_option
                ? justification.whyCorrect
                : justification[`why${key}IsWrong`]
              : null;
            return (
              <div key={key} className="space-y-1">
                <div
                  className={cx(
                    "flex items-start gap-2 rounded-lg border px-3 py-2 text-sm",
                    isKeyed && "border-signal-good/50 bg-signal-good/10 text-signal-good",
                    wasChosen && !isKeyed && "border-signal-bad/50 bg-signal-bad/10 text-signal-bad",
                    !wasChosen && !isKeyed && "border-cap-line bg-white text-cap-slate",
                  )}
                >
                  {isKeyed ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : null}
                  {wasChosen && !isKeyed ? <XCircle className="mt-0.5 h-4 w-4 shrink-0" /> : null}
                  {!wasChosen && !isKeyed ? <Circle className="mt-0.5 h-4 w-4 shrink-0 text-cap-line" /> : null}
                  <span className="flex-1"><span className="font-semibold">{key}.</span> {text}</span>
                  {wasChosen ? <span className="shrink-0 text-[11px] font-medium uppercase tracking-wide">your pick</span> : null}
                  {isKeyed && !wasChosen ? <span className="shrink-0 text-[11px] font-medium uppercase tracking-wide">keyed answer</span> : null}
                </div>
                {justNote ? (
                  <p className="pl-7 text-[11px] leading-relaxed text-cap-slate">{justNote}</p>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          {scored.rubric_dimensions.map((dimension) => (
            <div key={dimension.name}>
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-cap-ink">{dimension.name}</span>
                <span className="text-cap-slate">{toTen(dimension.score).toFixed(1)} / 10</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white">
                <span
                  className="block h-full rounded-full bg-cap-blue"
                  style={{ width: `${Math.min(100, Math.round(dimension.score * 100))}%` }}
                />
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-cap-slate">{dimension.note}</p>
            </div>
          ))}
        </div>
      )}

      <p className="mt-3 border-t border-cap-line pt-3 text-sm leading-relaxed text-cap-ink">{scored.feedback}</p>
    </div>
  );
}

const VERDICT_STYLE = {
  PASS: "border-signal-good/30 bg-signal-good/5 text-signal-good",
  FAIL: "border-signal-bad/30 bg-signal-bad/5 text-signal-bad",
  "REVIEW REQUIRED": "border-signal-warn/30 bg-signal-warn/5 text-signal-warn",
};

function PostInterviewReport({ report }) {
  const verdictStyle = VERDICT_STYLE[report.verdict] || "border-cap-line bg-white text-cap-slate";
  return (
    <BentoCard>
      <Eyebrow>Post-interview report</Eyebrow>
      <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
        How this round went, section by section
      </h3>

      <div className={`mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 ${verdictStyle}`}>
        <div>
          <p className="text-sm font-semibold">{report.verdict} - {report.raw_score_pct}% overall</p>
          <p className="mt-0.5 text-xs leading-relaxed opacity-80">{report.overall_feedback}</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium">{report.drive_benchmark.drive_label} cutoff</p>
          <p className="text-lg font-display font-semibold">{report.drive_benchmark.cutoff_pct}%</p>
          <p className="text-[11px] opacity-70">{report.drive_benchmark.note}</p>
        </div>
      </div>

      {report.section_breakdown?.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-cap-slate">Section breakdown</p>
          <div className="mt-2 space-y-2">
            {report.section_breakdown.map((sec) => (
              <div key={sec.section} className="flex items-center gap-3 rounded-xl border border-cap-line bg-white px-3.5 py-2.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-cap-ink truncate">{sec.section}</span>
                    <span className={cx(
                      "shrink-0 text-[11px] font-semibold",
                      sec.status === "STRONG" && "text-signal-good",
                      sec.status === "AVERAGE" && "text-signal-warn",
                      sec.status === "WEAK" && "text-signal-bad",
                    )}>{sec.status}</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-cap-mist">
                    <span
                      className={cx(
                        "block h-full rounded-full",
                        sec.status === "STRONG" && "bg-signal-good",
                        sec.status === "AVERAGE" && "bg-signal-warn",
                        sec.status === "WEAK" && "bg-signal-bad",
                      )}
                      style={{ width: `${sec.section_score_pct}%` }}
                    />
                  </div>
                </div>
                <span className="shrink-0 font-display text-sm font-semibold text-cap-navy">
                  {sec.section_score_pct}%
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {report.top_improvement_areas?.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-cap-slate">Where to focus next</p>
          <div className="mt-2 space-y-3">
            {report.top_improvement_areas.map((area) => (
              <div key={area.area} className="rounded-xl border border-cap-line bg-white p-3.5">
                <p className="text-sm font-semibold text-cap-navy">{area.area}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-cap-slate">{area.reason}</p>
                <ul className="mt-2 space-y-1">
                  {area.recommended_resources.map((res) => (
                    <li key={res} className="flex items-start gap-1.5 text-xs text-cap-blue">
                      <ChevronRight className="mt-0.5 h-3 w-3 shrink-0" />
                      {res}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </BentoCard>
  );
}

