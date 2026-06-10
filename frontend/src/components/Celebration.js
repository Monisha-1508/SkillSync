"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * A short-lived full-screen overlay of confetti and balloons - the visual
 * half of "you cleared it", sitting alongside whatever toast or card already
 * carries the words. Pure CSS transforms on a fixed set of absolutely
 * positioned pieces, each one given its own randomised lane, colour, delay
 * and spin the moment a burst starts; nothing here touches a canvas or a
 * third-party animation library, because two dozen divs with a `transform`
 * keyframe is already plenty for a moment that lasts four seconds.
 *
 * `variant` picks the mood: "confetti" for a brisk shower, "balloons" for a
 * slower, warmer rise, "sparks" for short bright streaks bursting outward
 * from scattered points, "both" for confetti-and-balloons together, and
 * "balloons-and-sparks" for the biggest moment this component knows -
 * balloons rising while sparks fly across the rest of the screen, the
 * "sparks flying all over" tier reserved for a checkpoint cleared at eighty
 * percent or better, one notch below the full "both" reserved for a
 * near-perfect sitting or finishing the whole roadmap outright.
 */
const PALETTE = ["#0070AD", "#17ABDA", "#001E3C", "#2BAE66", "#F2B705", "#E2725B"];

function randomBetween(min, max) {
  return min + Math.random() * (max - min);
}

function buildConfetti(count) {
  return Array.from({ length: count }, (_, index) => ({
    id: `c${index}`,
    left: randomBetween(2, 98),
    delay: randomBetween(0, 0.9),
    duration: randomBetween(2.6, 4.2),
    drift: randomBetween(-90, 90),
    spin: randomBetween(360, 900) * (Math.random() > 0.5 ? 1 : -1),
    color: PALETTE[index % PALETTE.length],
    width: randomBetween(6, 11),
    height: randomBetween(10, 16),
    radius: Math.random() > 0.5 ? "999px" : "3px",
  }));
}

function buildBalloons(count) {
  return Array.from({ length: count }, (_, index) => ({
    id: `b${index}`,
    left: randomBetween(8, 92),
    delay: randomBetween(0, 1.1),
    duration: randomBetween(4.2, 5.6),
    sway: randomBetween(-30, 30),
    color: PALETTE[(index + 2) % PALETTE.length],
  }));
}

function buildSparks(count) {
  return Array.from({ length: count }, (_, index) => {
    const angle = randomBetween(0, Math.PI * 2);
    const distance = randomBetween(70, 220);
    return {
      id: `s${index}`,
      top: randomBetween(8, 88),
      left: randomBetween(8, 92),
      delay: randomBetween(0, 1.3),
      duration: randomBetween(0.9, 1.7),
      x: Math.cos(angle) * distance,
      y: Math.sin(angle) * distance,
      rotate: randomBetween(0, 360),
      length: randomBetween(18, 34),
      color: PALETTE[index % PALETTE.length],
    };
  });
}

const _SPARK_VARIANTS = new Set(["sparks", "balloons-and-sparks"]);
const _BALLOON_VARIANTS = new Set(["balloons", "both", "balloons-and-sparks"]);
const _CONFETTI_VARIANTS = new Set(["confetti", "both"]);

export function Celebration({ active, variant = "confetti", durationMs = 4200, onDone }) {
  const [visible, setVisible] = useState(active);
  const confetti = useMemo(() => (_CONFETTI_VARIANTS.has(variant) ? buildConfetti(28) : []), [variant, active]);
  const balloons = useMemo(
    () => (_BALLOON_VARIANTS.has(variant) ? buildBalloons(variant === "both" ? 6 : 9) : []),
    [variant, active],
  );
  const sparks = useMemo(() => (_SPARK_VARIANTS.has(variant) ? buildSparks(16) : []), [variant, active]);

  useEffect(() => {
    if (!active) return undefined;
    setVisible(true);
    const timer = window.setTimeout(() => {
      setVisible(false);
      onDone?.();
    }, durationMs);
    return () => window.clearTimeout(timer);
  }, [active, durationMs, onDone]);

  if (!visible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[60] overflow-hidden" aria-hidden="true">
      {confetti.map((piece) => (
        <span
          key={piece.id}
          className="confetti-piece absolute top-0"
          style={{
            left: `${piece.left}%`,
            width: `${piece.width}px`,
            height: `${piece.height}px`,
            backgroundColor: piece.color,
            borderRadius: piece.radius,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duration}s`,
            "--drift": `${piece.drift}px`,
            "--spin": `${piece.spin}deg`,
          }}
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
            className="block h-12 w-10 rounded-[50%_50%_50%_50%/_60%_60%_40%_40%] shadow-[0_10px_24px_-12px_rgba(11,31,51,0.5)]"
            style={{ backgroundColor: balloon.color }}
          />
          <span className="h-8 w-px bg-cap-slate/40" />
        </span>
      ))}
      {sparks.map((spark) => (
        <span
          key={spark.id}
          className="spark-piece absolute block rounded-full"
          style={{
            top: `${spark.top}%`,
            left: `${spark.left}%`,
            width: `${spark.length}px`,
            height: "2.5px",
            backgroundColor: spark.color,
            boxShadow: `0 0 8px 1px ${spark.color}`,
            animationDelay: `${spark.delay}s`,
            animationDuration: `${spark.duration}s`,
            "--spark-x": `${spark.x}px`,
            "--spark-y": `${spark.y}px`,
            "--spark-rotate": `${spark.rotate}deg`,
          }}
        />
      ))}
    </div>
  );
}
