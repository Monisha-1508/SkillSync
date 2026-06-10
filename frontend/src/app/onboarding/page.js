"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X, ArrowRight, ArrowLeft, Loader2, LogIn } from "lucide-react";
import { Button, BentoCard, Eyebrow } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";

const ROLES = [
  "Software Development Engineer",
  "Data Analyst",
  "Capgemini Technology Analyst",
  "Data Scientist",
  "Full Stack Developer",
];

const PLACEMENT_MODES = [
  { value: "general", label: "General placement prep" },
  { value: "tcs_nqt", label: "TCS NQT" },
  { value: "infytq", label: "Infosys InfyTQ" },
  { value: "wipro_nlth", label: "Wipro NLTH" },
  { value: "cap_exceller", label: "Capgemini Exceller" },
];

const BACKGROUNDS = [
  { value: "cs", label: "Computer science / IT degree" },
  { value: "non_cs", label: "Other engineering or science degree" },
  { value: "diploma", label: "Diploma, lateral entry" },
  { value: "other", label: "Something else entirely" },
];

const BUDGET_MODES = [
  { value: "free", label: "Free resources only", hint: "every recommendation stays inside no-cost material" },
  { value: "paid", label: "Open to paid resources", hint: "the curator can also surface well-reviewed paid courses" },
];

const COMMON_SKILLS = [
  "Python", "SQL", "Java", "JavaScript", "Data Structures & Algorithms",
  "Object-Oriented Programming", "Excel", "Statistics", "System Design", "Communication",
];

const STEPS = ["About you", "Your skills", "Your week", "Review"];

function emptyForm() {
  return {
    name: "",
    target_role: ROLES[0],
    target_companies: "",
    weekly_hours: 12,
    deadline_weeks: 14,
    budget_mode: "free",
    placement_mode: "general",
    background: "cs",
  };
}

export default function OnboardingPage() {
  const router = useRouter();
  const { status, isSignedIn, user } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [skills, setSkills] = useState({ Python: 3, SQL: 2 });
  const [skillDraft, setSkillDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (status === "signed-out") router.replace("/login?next=/onboarding");
  }, [status, router]);

  useEffect(() => {
    if (isSignedIn && user?.name && !form.name) update("name", user.name);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSignedIn, user]);

  const canAdvance = useMemo(() => {
    if (step === 0) return form.name.trim().length > 0 && form.target_role.trim().length > 0;
    if (step === 1) return Object.keys(skills).length > 0;
    return true;
  }, [step, form, skills]);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function addSkill(label) {
    const trimmed = label.trim();
    if (!trimmed || skills[trimmed] !== undefined) return;
    setSkills((prev) => ({ ...prev, [trimmed]: 3 }));
    setSkillDraft("");
  }

  function setRating(name, rating) {
    setSkills((prev) => ({ ...prev, [name]: rating }));
  }

  function removeSkill(name) {
    setSkills((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: form.name.trim(),
        target_role: form.target_role,
        target_companies: form.target_companies
          .split(",")
          .map((entry) => entry.trim())
          .filter(Boolean),
        current_skills: skills,
        weekly_hours: Number(form.weekly_hours),
        deadline_weeks: Number(form.deadline_weeks),
        budget_mode: form.budget_mode,
        placement_mode: form.placement_mode,
        background: form.background,
      };
      const profile = await api.post("/profiles", payload);
      router.push(`/dashboard?profile=${profile.id}&fresh=1`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong sending that - check the backend is running and try again.");
      setSubmitting(false);
    }
  }

  if (status !== "signed-in") {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 py-14 text-center">
        <BentoCard className="max-w-sm">
          <LogIn className="mx-auto h-6 w-6 text-cap-blue" />
          <p className="mt-3 font-display text-lg font-semibold text-cap-navy">
            {status === "checking" ? "Checking your session..." : "Taking you to log in..."}
          </p>
          <p className="mt-2 text-sm text-cap-slate leading-relaxed">
            Building a plan needs an account, so it has somewhere to live the
            next time you come back for it.
          </p>
        </BentoCard>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-14">
      <Eyebrow>Three minutes, four short steps</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-semibold text-cap-navy">Let's map where you stand</h1>
      <p className="mt-3 max-w-xl text-cap-slate leading-relaxed">
        Nothing here is graded. The more honestly you rate yourself, the more
        useful the gap map - and the plan built on top of it - turns out to be.
      </p>

      <ol className="mt-8 flex items-center gap-2 text-xs font-medium text-cap-slate">
        {STEPS.map((label, index) => (
          <li key={label} className="flex items-center gap-2">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full border text-[12px] font-semibold ${
                index === step
                  ? "border-cap-blue bg-cap-blue text-white"
                  : index < step
                    ? "border-cap-blue/40 bg-cap-mist text-cap-blue"
                    : "border-cap-line bg-white text-cap-slate"
              }`}
            >
              {index + 1}
            </span>
            <span className={index === step ? "text-cap-navy" : ""}>{label}</span>
            {index < STEPS.length - 1 ? <span className="mx-1 h-px w-6 bg-cap-line" /> : null}
          </li>
        ))}
      </ol>

      <BentoCard className="mt-6">
        {step === 0 && <StepAbout form={form} update={update} />}
        {step === 1 && (
          <StepSkills
            skills={skills}
            skillDraft={skillDraft}
            setSkillDraft={setSkillDraft}
            addSkill={addSkill}
            setRating={setRating}
            removeSkill={removeSkill}
          />
        )}
        {step === 2 && <StepWeek form={form} update={update} />}
        {step === 3 && <StepReview form={form} skills={skills} />}

        {error ? (
          <p className="mt-6 rounded-xl border border-signal-bad/30 bg-signal-bad/10 px-4 py-3 text-sm text-signal-bad">
            {error}
          </p>
        ) : null}

        <div className="mt-8 flex items-center justify-between border-t border-cap-line pt-6">
          <Button
            variant="ghost"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className={step === 0 ? "invisible" : ""}
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button variant="primary" disabled={!canAdvance} onClick={() => setStep((s) => s + 1)}>
              Continue
              <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button variant="primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {submitting ? "Building your profile..." : "Build my plan"}
            </Button>
          )}
        </div>
      </BentoCard>
    </main>
  );
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-cap-navy">{label}</span>
      {hint ? <span className="mt-0.5 block text-xs text-cap-slate">{hint}</span> : null}
      <div className="mt-2">{children}</div>
    </label>
  );
}

const inputClass =
  "w-full rounded-xl border border-cap-line bg-white px-3.5 py-2.5 text-sm text-cap-ink " +
  "placeholder:text-cap-slate/60 focus:border-cap-blue focus:outline-none focus:ring-2 focus:ring-cap-blue/15";

function StepAbout({ form, update }) {
  return (
    <div className="space-y-5">
      <Field label="What should the plan call you?">
        <input
          className={inputClass}
          value={form.name}
          onChange={(event) => update("name", event.target.value)}
          placeholder="Your name"
        />
      </Field>
      <Field label="Which role are you preparing for?">
        <select className={inputClass} value={form.target_role} onChange={(event) => update("target_role", event.target.value)}>
          {ROLES.map((role) => (
            <option key={role} value={role}>{role}</option>
          ))}
        </select>
      </Field>
      <Field label="Companies on your shortlist" hint="Comma-separated - this only shapes which interview rounds get offered later">
        <input
          className={inputClass}
          value={form.target_companies}
          onChange={(event) => update("target_companies", event.target.value)}
          placeholder="TCS, Infosys, Capgemini"
        />
      </Field>
      <Field label="Which placement track are you aiming at?">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {PLACEMENT_MODES.map((mode) => (
            <RadioCard
              key={mode.value}
              active={form.placement_mode === mode.value}
              onClick={() => update("placement_mode", mode.value)}
              label={mode.label}
            />
          ))}
        </div>
      </Field>
      <Field label="What's your academic background?">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {BACKGROUNDS.map((bg) => (
            <RadioCard
              key={bg.value}
              active={form.background === bg.value}
              onClick={() => update("background", bg.value)}
              label={bg.label}
            />
          ))}
        </div>
      </Field>
    </div>
  );
}

function RadioCard({ active, onClick, label, hint }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
        active
          ? "border-cap-blue bg-cap-mist text-cap-navy font-medium"
          : "border-cap-line bg-white text-cap-slate hover:border-cap-blue/50"
      }`}
    >
      <span className="block">{label}</span>
      {hint ? <span className="mt-0.5 block text-xs text-cap-slate">{hint}</span> : null}
    </button>
  );
}

function StepSkills({ skills, skillDraft, setSkillDraft, addSkill, setRating, removeSkill }) {
  const entries = Object.entries(skills);
  const suggestions = COMMON_SKILLS.filter((name) => skills[name] === undefined);

  return (
    <div>
      <p className="text-sm text-cap-navy font-medium">Rate yourself on the skills you already have</p>
      <p className="mt-1 text-xs text-cap-slate">
        1 means "heard of it", 5 means "could explain it to someone else". The gap map reads the space between this and the role - rate honestly and it does its best work.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          className={`${inputClass} max-w-[220px]`}
          placeholder="Add a skill"
          value={skillDraft}
          onChange={(event) => setSkillDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addSkill(skillDraft);
            }
          }}
        />
        <Button variant="secondary" onClick={() => addSkill(skillDraft)}>
          <Plus className="h-4 w-4" />
          Add
        </Button>
      </div>

      {suggestions.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.slice(0, 6).map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => addSkill(name)}
              className="rounded-full border border-cap-line bg-white px-3 py-1 text-xs text-cap-slate hover:border-cap-blue hover:text-cap-blue"
            >
              + {name}
            </button>
          ))}
        </div>
      ) : null}

      <div className="mt-6 space-y-3">
        {entries.length === 0 ? (
          <p className="rounded-xl border border-dashed border-cap-line px-4 py-6 text-center text-sm text-cap-slate">
            Add at least one skill to continue - even a low rating is useful information.
          </p>
        ) : (
          entries.map(([name, rating]) => (
            <div key={name} className="flex items-center gap-3 rounded-xl border border-cap-line bg-white px-4 py-3">
              <span className="flex-1 text-sm font-medium text-cap-ink">{name}</span>
              <div className="flex items-center gap-1.5">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setRating(name, value)}
                    aria-label={`Rate ${name} ${value} out of 5`}
                    className={`h-7 w-7 rounded-full border text-xs font-semibold transition-colors ${
                      value <= rating
                        ? "border-cap-blue bg-cap-blue text-white"
                        : "border-cap-line bg-white text-cap-slate hover:border-cap-blue/40"
                    }`}
                  >
                    {value}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => removeSkill(name)}
                aria-label={`Remove ${name}`}
                className="rounded-full p-1.5 text-cap-slate hover:bg-cap-mist hover:text-signal-bad"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StepWeek({ form, update }) {
  return (
    <div className="space-y-6">
      <Field
        label={`Hours you can realistically give per week: ${form.weekly_hours}`}
        hint="Be conservative - the roadmap is built around this number, and a plan that assumes more than you have is the one that gets abandoned"
      >
        <input
          type="range"
          min="1"
          max="40"
          value={form.weekly_hours}
          onChange={(event) => update("weekly_hours", event.target.value)}
          className="w-full accent-cap-blue"
        />
      </Field>
      <Field
        label={`Weeks until your target date: ${form.deadline_weeks}`}
        hint="A test date, an application deadline, or just a date you'd like to feel ready by"
      >
        <input
          type="range"
          min="2"
          max="52"
          value={form.deadline_weeks}
          onChange={(event) => update("deadline_weeks", event.target.value)}
          className="w-full accent-cap-blue"
        />
      </Field>
      <Field label="How should the resource curator pick material for you?">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {BUDGET_MODES.map((mode) => (
            <RadioCard
              key={mode.value}
              active={form.budget_mode === mode.value}
              onClick={() => update("budget_mode", mode.value)}
              label={mode.label}
              hint={mode.hint}
            />
          ))}
        </div>
      </Field>
    </div>
  );
}

function StepReview({ form, skills }) {
  const rows = [
    ["Name", form.name || "-"],
    ["Target role", form.target_role],
    ["Target companies", form.target_companies || "not specified"],
    ["Placement track", PLACEMENT_MODES.find((m) => m.value === form.placement_mode)?.label],
    ["Background", BACKGROUNDS.find((b) => b.value === form.background)?.label],
    ["Hours per week", `${form.weekly_hours}h`],
    ["Runway", `${form.deadline_weeks} weeks`],
    ["Resource budget", BUDGET_MODES.find((m) => m.value === form.budget_mode)?.label],
  ];
  return (
    <div>
      <p className="text-sm text-cap-navy font-medium">Here's what the six agents are about to read</p>
      <p className="mt-1 text-xs text-cap-slate">
        Submitting kicks off the pipeline - the dashboard streams each agent's
        step live, so the next thing you'll see is the gap map taking shape.
      </p>
      <dl className="mt-5 divide-y divide-cap-line rounded-xl border border-cap-line bg-white">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
            <dt className="text-cap-slate">{label}</dt>
            <dd className="text-right font-medium text-cap-ink">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-4 rounded-xl border border-cap-line bg-cap-mist/60 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-cap-slate">Self-rated skills</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(skills).map(([name, rating]) => (
            <span key={name} className="rounded-full border border-cap-line bg-white px-3 py-1 text-xs text-cap-ink">
              {name} - {rating}/5
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
