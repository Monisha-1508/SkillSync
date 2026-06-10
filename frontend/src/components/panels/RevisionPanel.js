"use client";

import { useState } from "react";
import { Layers, CalendarClock, Sparkles, RotateCw, Loader2, CheckCircle2 } from "lucide-react";
import { BentoCard, Eyebrow, Button, StatusPill } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/cx";

const _RATINGS = [
  { rating: 1, label: "Again", hint: "didn't land - ask again soon", tone: "border-signal-bad/40 bg-signal-bad/10 text-signal-bad hover:bg-signal-bad/20" },
  { rating: 2, label: "Hard", hint: "got there, but it took real effort", tone: "border-signal-warn/40 bg-signal-warn/10 text-signal-warn hover:bg-signal-warn/20" },
  { rating: 3, label: "Good", hint: "recalled it at a normal pace", tone: "border-cap-vibrant/40 bg-cap-vibrant/10 text-cap-vibrant hover:bg-cap-vibrant/20" },
  { rating: 4, label: "Easy", hint: "barely had to think about it", tone: "border-signal-good/40 bg-signal-good/10 text-signal-good hover:bg-signal-good/20" },
];

export function RevisionPanel({ revision, profileId, onReviewed }) {
  const [queue, setQueue] = useState(null);
  const [position, setPosition] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [grading, setGrading] = useState(null);
  const [error, setError] = useState("");
  const [gradedCount, setGradedCount] = useState(0);

  const current = queue && position < queue.length ? queue[position] : null;
  const finished = queue !== null && current === null;

  async function openDeck(scope = "due") {
    setLoading(true);
    setError("");
    try {
      const deck = await api.get(`/revision/${profileId}/deck`);
      const cards = deck.cards || [];
      const dueCards = cards.filter((card) => card.is_due);
      const showFull = scope === "all" || dueCards.length === 0;
      setQueue(showFull ? cards : dueCards);
      setPosition(0);
      setRevealed(false);
      setGradedCount(0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open the deck just now - try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  async function grade(rating) {
    if (!current || grading !== null) return;
    setGrading(rating);
    setError("");
    try {
      await api.post(`/revision/${profileId}/review`, { card_id: current.id, rating });
      setGradedCount((count) => count + 1);
      setPosition((index) => index + 1);
      setRevealed(false);
      onReviewed?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That grade did not save - the deck has not moved on, give it another try.");
    } finally {
      setGrading(null);
    }
  }

  function restart() {
    setQueue(null);
    setPosition(0);
    setRevealed(false);
    setError("");
    setGradedCount(0);
  }

  return (
    <div className="bento-grid grid-cols-1 lg:grid-cols-3">
      <BentoCard className="flex flex-col items-start gap-2">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-cap-mist text-cap-blue">
          <Layers className="h-5 w-5" />
        </span>
        <p className="font-display text-2xl font-semibold text-cap-navy">{revision.total_cards}</p>
        <p className="text-sm text-cap-slate">cards in the deck overall, drawn from the skills already on the plan</p>
      </BentoCard>

      <BentoCard className="flex flex-col items-start gap-2">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-cap-mist text-cap-blue">
          <CalendarClock className="h-5 w-5" />
        </span>
        <p className="font-display text-2xl font-semibold text-cap-navy">{revision.due_now}</p>
        <p className="text-sm text-cap-slate">due for review right now under the spaced-repetition schedule</p>
      </BentoCard>

      <BentoCard className="lg:col-span-1">
        <Eyebrow>Up next</Eyebrow>
        <ul className="mt-3 space-y-2.5">
          {revision.next_due.length === 0 ? (
            <li className="flex items-center gap-2 text-sm text-cap-slate">
              <Sparkles className="h-4 w-4" />
              Nothing due right now - the deck is caught up.
            </li>
          ) : (
            revision.next_due.map((card) => (
              <li key={card.id} className="rounded-xl border border-cap-line bg-white px-3.5 py-2.5">
                <p className="text-xs font-semibold text-cap-blue">{card.skill_name}</p>
                <p className="mt-1 text-sm text-cap-ink">{card.front}</p>
                <p className="mt-1 text-[11px] text-cap-slate">due {new Date(card.due_date).toLocaleDateString()}</p>
              </li>
            ))
          )}
        </ul>
      </BentoCard>

      <BentoCard className="lg:col-span-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Eyebrow>Sit the deck</Eyebrow>
            <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">
              Read the front, say the answer out loud, then grade yourself honestly
            </h3>
            <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-cap-slate">
              This is also the one thing a low checkpoint score asks for before
              it offers a retake - working back through that week&apos;s cards
              here is what moves &quot;reviewed since the last sitting&quot;
              from zero towards the number the checkpoint board is waiting on.
            </p>
          </div>
          {queue !== null ? (
            <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={restart}>
              <RotateCw className="h-3.5 w-3.5" />
              Start over
            </Button>
          ) : null}
        </div>

        {error ? (
          <p className="mt-3 rounded-xl border border-signal-bad/30 bg-signal-bad/5 px-3.5 py-2.5 text-sm text-signal-bad">
            {error}
          </p>
        ) : null}

        <div className="mt-4">
          {queue === null ? (
            <div className="flex flex-col items-start gap-2.5">
              <Button onClick={() => openDeck("due")} disabled={loading} className="text-sm">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {revision.due_now > 0 ? `Review the ${revision.due_now} card${revision.due_now === 1 ? "" : "s"} due now` : "Open the deck anyway"}
              </Button>
              {revision.due_now > 0 ? (
                <button
                  type="button"
                  onClick={() => openDeck("all")}
                  disabled={loading}
                  className="text-xs font-medium text-cap-blue hover:underline disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Or open every card in the deck - useful if a checkpoint retake is waiting on one that is not due yet
                </button>
              ) : null}
            </div>
          ) : finished ? (
            <div className="flex items-center gap-3 rounded-xl border border-signal-good/30 bg-signal-good/5 px-4 py-3.5">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-signal-good" />
              <p className="text-sm text-cap-ink">
                {gradedCount === 0
                  ? "That sitting closed without grading anything - the deck is open again whenever you are ready for another pass."
                  : `Graded ${gradedCount} card${gradedCount === 1 ? "" : "s"} this round - FSRS has already rebooked each one onto its next due date.`}
                {" "}Come back when the next batch is due, or revisit any week&apos;s skills again from here.
              </p>
            </div>
          ) : current ? (
            <div className="rounded-2xl border border-cap-line bg-cap-cloud/60 p-5">
              <div className="flex items-center justify-between gap-3">
                <span className="rounded-full border border-cap-line bg-white px-2.5 py-1 text-[11px] font-medium text-cap-slate">
                  card {position + 1} of {queue.length}
                </span>
                <span className="text-xs font-semibold uppercase tracking-wide text-cap-blue">{current.skill_name}</span>
              </div>
              <p className="mt-4 font-display text-lg font-semibold text-cap-navy">{current.front}</p>

              {revealed ? (
                <>
                  <div className="mt-3 rounded-xl border border-cap-line bg-white px-4 py-3 text-sm leading-relaxed text-cap-ink">
                    {current.back}
                  </div>
                  <p className="mt-4 text-xs font-medium uppercase tracking-wide text-cap-slate">How did that go</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {_RATINGS.map((option) => (
                      <button
                        key={option.rating}
                        type="button"
                        disabled={grading !== null}
                        onClick={() => grade(option.rating)}
                        title={option.hint}
                        className={cx(
                          "flex flex-col items-center gap-0.5 rounded-xl border px-2.5 py-2.5 text-xs font-semibold transition-colors",
                          option.tone,
                          grading !== null && "cursor-not-allowed opacity-60",
                        )}
                      >
                        {grading === option.rating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : option.label}
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <Button variant="secondary" className="mt-4 text-sm" onClick={() => setRevealed(true)}>
                  Reveal the answer
                </Button>
              )}
            </div>
          ) : null}
        </div>
      </BentoCard>
    </div>
  );
}
