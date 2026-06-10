"use client";

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { BentoCard, Eyebrow, StatusPill } from "@/components/ui";

/**
 * The gap map is the system's first opinion about the learner, and the one
 * every later panel quietly assumes - so it gets the most literal treatment
 * possible: four labelled buckets, a radar of the families they cluster
 * into, and the confidence disclosure shown next to the claim it qualifies
 * rather than buried in a tooltip.
 */
const BUCKET_META = {
  covered: { label: "Covered", status: "good", copy: "Rated highly enough, or implied strongly enough by something that was, to count as in hand." },
  developing: { label: "Developing", status: "warn", copy: "A middling self-rating, or close enough to something covered to read as partway there." },
  gap: { label: "Gap", status: "bad", copy: "Low-rated or unrated and not implied by anything else - this is where the plan should spend its hours." },
  unknown: { label: "Unrated", status: "unknown", copy: "Never came up in the intake, and nothing nearby implies it either way." },
};

export function GapMapPanel({ gapMap }) {
  return (
    <div className="bento-grid grid-cols-1 lg:grid-cols-3">
      <BentoCard className="lg:col-span-1">
        <Eyebrow>How the radar reads</Eyebrow>
        <h3 className="mt-1 font-display text-base font-semibold text-cap-navy">Mastery by skill family</h3>
        <p className="mt-2 text-xs leading-relaxed text-cap-slate">
          Each axis averages the mastery score across every skill in that
          family the role actually needs - a wide shape means broad footing,
          a narrow one names exactly where the role and the learner currently disagree.
        </p>
        <div className="mt-2 h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={gapMap.radar_axes} outerRadius="72%">
              <PolarGrid stroke="#D7E4ED" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: "#5B7184", fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 5]} tick={{ fill: "#8895A7", fontSize: 10 }} tickCount={6} />
              <Radar dataKey="score" stroke="#0070AD" fill="#17ABDA" fillOpacity={0.35} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-2 rounded-xl border border-cap-line bg-cap-mist/60 px-3 py-2 text-xs leading-relaxed text-cap-slate">
          <span className="font-semibold text-cap-ink">{gapMap.disclosure.label}: </span>
          {gapMap.disclosure.message}
        </p>
      </BentoCard>

      <div className="bento-grid grid-cols-1 sm:grid-cols-2 lg:col-span-2">
        {Object.entries(BUCKET_META).map(([key, meta]) => (
          <BentoCard key={key}>
            <div className="flex items-center justify-between">
              <StatusPill status={meta.status}>{meta.label}</StatusPill>
              <span className="font-display text-xl font-semibold text-cap-navy">{gapMap.counts[key]}</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-cap-slate">{meta.copy}</p>
            <ul className="mt-3 max-h-44 space-y-1.5 overflow-y-auto scrollbar-thin pr-1">
              {gapMap[key].length === 0 ? (
                <li className="text-xs text-cap-slate/70">Nothing landed in this bucket.</li>
              ) : (
                gapMap[key].map((item) => (
                  <li key={item.skill_id} className="flex items-center justify-between rounded-lg border border-cap-line bg-white px-3 py-1.5 text-xs">
                    <span className="text-cap-ink">{item.name}</span>
                    <span className="text-cap-slate">{item.rating ? `self-rated ${item.rating}/5` : item.source}</span>
                  </li>
                ))
              )}
            </ul>
          </BentoCard>
        ))}
      </div>
    </div>
  );
}
