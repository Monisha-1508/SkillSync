"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";

const PASS_THRESHOLD = {
  CHECKPOINT: 50,
  MOCK_INTERVIEW: 60,
};

const ACCENT = {
  CHECKPOINT: {
    color: "#4D96FF",
    ringColor: "#4D96FF",
    gradient: "linear-gradient(135deg, #4D96FF 0%, #38D9A9 100%)",
  },
  MOCK_INTERVIEW: {
    color: "#CC5DE8",
    ringColor: "#CC5DE8",
    gradient: "linear-gradient(135deg, #CC5DE8 0%, #FF6B6B 100%)",
  },
};

const BADGE_TEXT = {
  CHECKPOINT: "Weekly Checkpoint Passed",
  MOCK_INTERVIEW: "Mock Interview Passed",
};

const UNLOCK_TEXT = {
  CHECKPOINT: "Next module unlocked",
  MOCK_INTERVIEW: "Drive readiness improved",
};

const BALLOON_COLORS = [
  "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF",
  "#FF922B", "#CC5DE8", "#F783AC", "#38D9A9",
];

const CONFETTI_COLORS = [
  "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#FF922B",
  "#CC5DE8", "#F783AC", "#38D9A9", "#ffffff", "#FFC9C9",
];

const SPARKLE_COLORS = ["#FFD700", "#FFF176", "#FFECB3", "#ffffff", "#FFD93D"];

const FIREWORK_RINGS = [
  { id: "fw0", top: "8%",  left: "8%",  color: "#FFD93D", delay: 0 },
  { id: "fw1", top: "8%",  left: "92%", color: "#FF6B6B", delay: 0.2 },
  { id: "fw2", top: "88%", left: "8%",  color: "#CC5DE8", delay: 0.4 },
  { id: "fw3", top: "88%", left: "92%", color: "#6BCB77", delay: 0.6 },
];

function rand(min, max) {
  return min + Math.random() * (max - min);
}

function buildBalloons() {
  return Array.from({ length: 18 }, (_, i) => ({
    id: `b${i}`,
    left: rand(5, 95),
    delay: rand(0, 2.5),
    duration: rand(4, 8),
    sway: rand(20, 50) * (Math.random() > 0.5 ? 1 : -1),
    scale: rand(0.7, 1.3),
    color: BALLOON_COLORS[i % BALLOON_COLORS.length],
  }));
}

const CONFETTI_SHAPES = ["circle", "rect", "diamond"];

function buildConfetti() {
  return Array.from({ length: 120 }, (_, i) => ({
    id: `c${i}`,
    left: rand(2, 98),
    delay: rand(0, 3),
    duration: rand(2.5, 5),
    drift: rand(-90, 90),
    spin: rand(180, 720) * (Math.random() > 0.5 ? 1 : -1),
    color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
    shape: CONFETTI_SHAPES[i % CONFETTI_SHAPES.length],
    size: rand(7, 14),
  }));
}

function buildSparkles() {
  return Array.from({ length: 40 }, (_, i) => ({
    id: `s${i}`,
    top: rand(5, 85),
    left: rand(5, 95),
    delay: rand(0, 3),
    duration: rand(1, 2.5),
    scale: rand(0.5, 1.8),
    color: SPARKLE_COLORS[i % SPARKLE_COLORS.length],
    char: i % 2 === 0 ? "✦" : "✧",
  }));
}

function passesProctoringGate(log) {
  if (!log) return true;
  const {
    copyPasteAttempts = 0,
    tabSwitches = 0,
    tabSwitchCount,
    fullscreenBreached = false,
    fullScreenMaintained,
  } = log;
  const tabs = tabSwitchCount ?? tabSwitches;
  const fsBreached = fullscreenBreached || fullScreenMaintained === false;
  if (copyPasteAttempts > 0) return false;
  if (tabs > 3) return false;
  if (fsBreached) return false;
  return true;
}

function ScoreRing({ score, ringColor }) {
  const r = 48;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.min(Math.max(score, 0), 100) / 100);
  return (
    <svg
      width="130"
      height="130"
      viewBox="0 0 120 120"
      className="block shrink-0"
      aria-label={`Score ${score} percent`}
    >
      <circle cx="60" cy="60" r={r} fill="none" stroke="#EFF2F5" strokeWidth="10" />
      <circle
        cx="60"
        cy="60"
        r={r}
        fill="none"
        stroke={ringColor}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform="rotate(-90 60 60)"
        style={{
          transition: "stroke-dashoffset 1.5s cubic-bezier(0.22, 1, 0.36, 1)",
          filter: `drop-shadow(0 0 7px ${ringColor}99)`,
        }}
      />
      <text
        x="60" y="54"
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="22"
        fontWeight="700"
        fill="#001E3C"
        fontFamily="Space Grotesk, system-ui, sans-serif"
      >
        {score}%
      </text>
      <text
        x="60" y="73"
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="9"
        fontWeight="500"
        fill="#5B7184"
        fontFamily="Inter, system-ui, sans-serif"
        letterSpacing="0.07em"
      >
        SCORE
      </text>
    </svg>
  );
}

function confettiStyle(piece) {
  const base = {
    backgroundColor: piece.color,
    width: `${piece.size}px`,
    height: `${piece.size}px`,
    animationDelay: `${piece.delay}s`,
    animationDuration: `${piece.duration}s`,
    "--drift": `${piece.drift}px`,
    "--spin": `${piece.spin}deg`,
  };
  if (piece.shape === "circle") {
    return { ...base, borderRadius: "50%" };
  }
  if (piece.shape === "diamond") {
    return { ...base, borderRadius: "2px", transform: "rotate(45deg)" };
  }
  return { ...base, height: `${piece.size * 1.65}px`, borderRadius: "2px" };
}

export function GamificationReward({ active, assessmentType, finalScore, proctoringLog, onDone }) {
  const [mounted, setMounted] = useState(false);

  const threshold = PASS_THRESHOLD[assessmentType] ?? 50;
  const passes = finalScore >= threshold;
  const proctor = passesProctoringGate(proctoringLog);
  const shouldShow = active && passes && proctor;

  const accent = ACCENT[assessmentType] || ACCENT.CHECKPOINT;
  const badgeText = BADGE_TEXT[assessmentType] || "Assessment Passed";
  const unlockText = UNLOCK_TEXT[assessmentType] || "Achievement unlocked";
  const scoreMessage =
    `You cleared the ${assessmentType === "CHECKPOINT" ? "Weekly Checkpoint" : "Mock Interview"} ` +
    `with a score of ${finalScore}%, beating the pass mark of ${threshold}%.`;

  const balloons = useMemo(buildBalloons, [active]);
  const confetti = useMemo(buildConfetti, [active]);
  const sparkles = useMemo(buildSparkles, [active]);

  useEffect(() => {
    if (!shouldShow) {
      setMounted(false);
      return;
    }
    setMounted(true);
  }, [shouldShow]);

  function dismiss() {
    setMounted(false);
    onDone?.();
  }

  if (!mounted) return null;

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Celebration"
    >
      <div
        className="absolute inset-0 bg-cap-navy/60 backdrop-blur-[3px]"
        onClick={dismiss}
        aria-hidden="true"
      />

      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">

        {confetti.map((piece) => (
          <span
            key={piece.id}
            className="confetti-piece absolute top-0"
            style={confettiStyle(piece)}
          />
        ))}

        {balloons.map((balloon) => (
          <span
            key={balloon.id}
            className="balloon-piece absolute bottom-0 flex flex-col items-center"
            style={{
              left: `${balloon.left}%`,
              animationDelay: `${balloon.delay}s`,
              animationDuration: `${balloon.duration}s`,
              "--sway": `${balloon.sway}px`,
            }}
          >
            <span
              className="block rounded-[50%_50%_50%_50%/_60%_60%_40%_40%] shadow-[0_8px_22px_-10px_rgba(11,31,51,0.45)]"
              style={{
                backgroundColor: balloon.color,
                width: `${40 * balloon.scale}px`,
                height: `${52 * balloon.scale}px`,
              }}
            />
            <span
              className="w-px"
              style={{
                height: `${28 * balloon.scale}px`,
                backgroundColor: `${balloon.color}90`,
              }}
            />
          </span>
        ))}

        {sparkles.map((spark) => (
          <span
            key={spark.id}
            className="sparkle-pulse absolute leading-none"
            style={{
              top: `${spark.top}%`,
              left: `${spark.left}%`,
              color: spark.color,
              fontSize: `${Math.round(18 * spark.scale)}px`,
              textShadow: `0 0 6px ${spark.color}`,
              animationDelay: `${spark.delay}s`,
              animationDuration: `${spark.duration}s`,
            }}
          >
            {spark.char}
          </span>
        ))}

        {FIREWORK_RINGS.map((ring) => (
          <span
            key={ring.id}
            className="firework-ring absolute rounded-full"
            style={{
              top: ring.top,
              left: ring.left,
              width: "180px",
              height: "180px",
              marginTop: "-90px",
              marginLeft: "-90px",
              borderColor: ring.color,
              animationDelay: `${ring.delay}s`,
              animationDuration: "1s",
            }}
          />
        ))}
      </div>

      <div className="reward-card-enter relative z-10 w-full max-w-sm rounded-2xl bg-white shadow-[0_32px_80px_-18px_rgba(11,31,51,0.60)]">
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss"
          className="absolute right-3 top-3 rounded-full p-1.5 text-cap-slate transition-colors hover:bg-cap-mist hover:text-cap-ink"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="px-6 pb-7 pt-8">
          <div className="flex justify-center">
            <span
              className="trophy-pendulum text-5xl"
              style={{ filter: "drop-shadow(0 0 12px #FFD700) drop-shadow(0 0 24px #FFD70055)" }}
            >
              🏆
            </span>
          </div>

          <h2 className="congrats-shimmer mt-4 text-center font-display text-2xl font-bold leading-tight">
            Congratulations!
          </h2>

          <div className="mt-3 flex justify-center">
            <span
              className="inline-flex items-center rounded-full px-3.5 py-1 text-xs font-semibold"
              style={{
                color: accent.color,
                backgroundColor: `${accent.color}16`,
                border: `1px solid ${accent.color}45`,
              }}
            >
              {badgeText}
            </span>
          </div>

          <div className="mt-4 flex justify-center">
            <ScoreRing score={finalScore} ringColor={accent.ringColor} />
          </div>

          <p className="mt-3 text-center text-[13px] leading-relaxed text-cap-slate">
            {scoreMessage}
          </p>

          <div className="mt-3 flex justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-signal-good/35 bg-signal-good/10 px-3.5 py-1.5 text-xs font-semibold text-signal-good">
              <span className="relative flex h-2 w-2 shrink-0">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal-good opacity-55" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-signal-good" />
              </span>
              {unlockText}
            </span>
          </div>

          <button
            type="button"
            onClick={dismiss}
            className="mt-5 w-full rounded-xl py-2.5 text-sm font-semibold text-white shadow-md transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0"
            style={{ background: accent.gradient }}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
