"use client";

import { useMemo } from "react";
import { ExternalLink, ShieldCheck, IndianRupee, Gift, Lock, Clock } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { BentoCard, Eyebrow, StatusPill } from "@/components/ui";

function trustStatus(score) {
  if (score >= 0.8) return "good";
  if (score >= 0.6) return "warn";
  return "bad";
}

export function ResourcesPanel({ resourcePicks, curation, resourceLock }) {
  const skillIds = Object.keys(resourcePicks);
  const allEntries = useMemo(() => skillIds.flatMap((id) => resourcePicks[id]), [resourcePicks, skillIds]);
  const lockedWeeks = resourceLock?.locked_weeks || [];
  const isPaidMode = curation?.budget_mode === "paid";

  const costMix = useMemo(() => {
    const free = allEntries.filter((entry) => entry.cost === "free").length;
    const paid = allEntries.length - free;
    return [
      { name: "Free", value: free, color: "#1f9d6f" },
      { name: "Paid", value: paid, color: "#0070AD" },
    ].filter((slice) => slice.value > 0);
  }, [allEntries]);

  const trustBuckets = useMemo(() => {
    const buckets = [
      { label: "0.8 - 1.0", min: 0.8, count: 0, color: "#1f9d6f" },
      { label: "0.6 - 0.79", min: 0.6, count: 0, color: "#e0a82e" },
      { label: "below 0.6", min: 0, count: 0, color: "#d8584f" },
    ];
    for (const entry of allEntries) {
      const bucket = buckets.find((b) => entry.trust_score >= b.min);
      if (bucket) bucket.count += 1;
    }
    return buckets;
  }, [allEntries]);

  return (
    <div className="space-y-6">
      <BentoCard className="flex flex-wrap items-center gap-6">
        <div>
          <Eyebrow>Curation, at a glance</Eyebrow>
          <p className="mt-1 text-sm text-cap-ink">
            Average trust score across every pick: <span className="font-semibold">{curation.average_trust.toFixed(2)}</span>
            {" "}(floor {curation.trust_floor.toFixed(2)})
          </p>
          <p className="mt-1 flex items-center gap-1.5 text-xs text-cap-slate">
            {isPaidMode ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-cap-blue/30 bg-cap-blue/10 px-2 py-0.5 text-[11px] font-medium text-cap-blue">
                <IndianRupee className="h-3 w-3" />
                Paid mode - premium resources prioritised, free resources as fallback
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-signal-good/30 bg-signal-good/10 px-2 py-0.5 text-[11px] font-medium text-signal-good">
                <Gift className="h-3 w-3" />
                Free mode - only no-cost resources shown
              </span>
            )}
          </p>
        </div>
        {curation.below_floor_excluded > 0 ? (
          <StatusPill status="warn">{curation.below_floor_excluded} resource(s) excluded for sitting below the trust floor</StatusPill>
        ) : (
          <StatusPill status="good">Nothing in the corpus needed to be excluded</StatusPill>
        )}
      </BentoCard>

      {allEntries.length > 0 ? (
        <div className="bento-grid grid-cols-1 sm:grid-cols-2">
          <BentoCard className="flex items-center gap-5">
            <div className="h-32 w-32 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={costMix} dataKey="value" innerRadius={38} outerRadius={58} stroke="none">
                    {costMix.map((slice) => (
                      <Cell key={slice.name} fill={slice.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div>
              <Eyebrow>Free vs paid mix</Eyebrow>
              <p className="mt-1 text-sm text-cap-ink">
                {costMix.map((slice, index) => (
                  <span key={slice.name}>
                    {index > 0 ? " · " : ""}
                    <span className="font-semibold" style={{ color: slice.color }}>{slice.value}</span> {slice.name.toLowerCase()}
                  </span>
                ))}
              </p>
              <p className="mt-1 text-xs text-cap-slate">
                across {allEntries.length} curated picks for {skillIds.length} scheduled skills
              </p>
            </div>
          </BentoCard>

          <BentoCard>
            <Eyebrow>Where the trust scores land</Eyebrow>
            <p className="mt-1 text-sm text-cap-ink">How many picks sit in each confidence band</p>
            <div className="mt-3 h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trustBuckets} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="4 6" stroke="#e3e9f1" horizontal={false} />
                  <XAxis type="number" hide allowDecimals={false} />
                  <YAxis type="category" dataKey="label" width={72} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip
                    cursor={{ fill: "#eef3f8" }}
                    formatter={(value) => [`${value} resource(s)`, ""]}
                    contentStyle={{ borderRadius: 12, border: "1px solid #e3e9f1", fontSize: 12 }}
                  />
                  <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={16}>
                    {trustBuckets.map((bucket) => (
                      <Cell key={bucket.label} fill={bucket.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </BentoCard>
        </div>
      ) : null}

      <div className="bento-grid grid-cols-1 lg:grid-cols-2">
        {skillIds.length === 0 && lockedWeeks.length === 0 ? (
          <BentoCard className="lg:col-span-2 text-center text-sm text-cap-slate">
            No scheduled skills to curate against yet - this fills in once the roadmap has working weeks.
          </BentoCard>
        ) : (
          skillIds.map((skillId) => (
            <BentoCard key={skillId}>
              <p className="text-xs font-semibold uppercase tracking-wide text-cap-slate">{skillId}</p>
              <ul className="mt-3 space-y-3">
                {resourcePicks[skillId].map((entry) => (
                  <li key={entry.resource_id} className="rounded-xl border border-cap-line bg-white p-3.5">
                    <div className="flex items-start justify-between gap-3">
                      <a
                        href={entry.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 text-sm font-medium text-cap-blue hover:underline"
                      >
                        {entry.title}
                        <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                      </a>
                      <StatusPill status={trustStatus(entry.trust_score)}>
                        <ShieldCheck className="h-3 w-3" />
                        {entry.trust_score.toFixed(2)}
                      </StatusPill>
                    </div>
                    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-cap-slate">
                      {entry.cost === "free" ? <Gift className="h-3.5 w-3.5" /> : <IndianRupee className="h-3.5 w-3.5" />}
                      {entry.cost}
                    </p>
                    <p className="mt-2 text-xs leading-relaxed text-cap-ink">{entry.why}</p>
                  </li>
                ))}
              </ul>
            </BentoCard>
          ))
        )}
        {lockedWeeks.map((week) => (
          <LockedWeekCard key={`locked-${week.week}`} week={week} />
        ))}
      </div>
    </div>
  );
}

/**
 * What a learner sees instead of a week's resource list while that week is
 * still behind the chain - not an empty gap that looks like a loading
 * glitch, but a clear, named reason: this is waiting on the week in front
 * of it being logged done, and the moment that happens these same slots
 * fill in with curated picks the same way this week's did.
 */
function LockedWeekCard({ week }) {
  return (
    <BentoCard className="border-dashed bg-cap-mist/30">
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cap-mist text-cap-slate">
          <Lock className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-cap-slate">Week {week.week} - locked for now</p>
          <p className="mt-1.5 text-xs leading-relaxed text-cap-ink">
            These resources open up once the week ahead of this one is logged done and its
            checkpoint is cleared - the same chain that gates the checkpoint board itself.
          </p>
          {week.skill_ids?.length ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {week.skill_ids.map((id) => (
                <span key={id} className="rounded-full border border-cap-line bg-white px-2 py-0.5 text-[11px] text-cap-slate">
                  {id}
                </span>
              ))}
            </div>
          ) : null}
          <p className="mt-2 flex items-center gap-1.5 text-xs text-cap-slate">
            <Clock className="h-3.5 w-3.5" />
            About {week.hours}h waiting behind the lock
          </p>
        </div>
      </div>
    </BentoCard>
  );
}
