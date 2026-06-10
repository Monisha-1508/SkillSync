"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, LogIn, UserPlus, Sparkles, ArrowRight, Radar } from "lucide-react";
import Link from "next/link";
import { Button, BentoCard, Eyebrow } from "@/components/ui";
import { useAuth, ApiError } from "@/lib/AuthContext";

const inputClass =
  "w-full rounded-xl border border-cap-line bg-white px-3.5 py-2.5 text-sm text-cap-ink " +
  "placeholder:text-cap-slate/60 focus:border-cap-blue focus:outline-none focus:ring-2 focus:ring-cap-blue/15";

const DEMO_EMAIL = "demo@skillsync.ai";
const DEMO_PASSWORD = "skillsync-demo";

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-cap-navy">{label}</span>
      <div className="mt-2">{children}</div>
    </label>
  );
}

function LoginContent() {
  const [mode, setMode] = useState("login");
  const router = useRouter();
  const params = useSearchParams();
  const { login, register } = useAuth();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  function destinationAfterAuth() {
    const back = params.get("next");
    return back && back.startsWith("/") ? back : "/plans";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(form.email.trim(), form.password);
      } else {
        await register(form.name.trim(), form.email.trim(), form.password);
      }
      router.push(destinationAfterAuth());
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Couldn't reach the backend just now - check it's running and try again.",
      );
      setSubmitting(false);
    }
  }

  async function fillDemoAndSignIn() {
    setMode("login");
    setForm({ name: "", email: DEMO_EMAIL, password: DEMO_PASSWORD });
    setSubmitting(true);
    setError(null);
    try {
      await login(DEMO_EMAIL, DEMO_PASSWORD);
      router.push(destinationAfterAuth());
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Couldn't reach the backend just now - check it's running and try again.",
      );
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-14">
      <Link href="/" className="mb-8 inline-flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cap-blue text-white">
          <Radar className="h-5 w-5" strokeWidth={2.25} />
        </span>
        <span className="font-display text-lg font-semibold text-cap-navy">SkillSync AI</span>
      </Link>

      <div className="grid gap-8 md:grid-cols-2 md:items-start">
        <div>
          <Eyebrow>One account, every plan you build</Eyebrow>
          <h1 className="mt-2 font-display text-3xl font-semibold text-cap-navy">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mt-3 max-w-md text-cap-slate leading-relaxed">
            {mode === "login"
              ? "Sign in to reach every plan you have already built, see how far you have come on each, and start a new one whenever a different goal calls for it."
              : "One login is all it takes. Once you are in, build as many plans as you need - one for this term's placement drive, another for a stretch role next year - and they will all be waiting for you here."}
          </p>

          <BentoCard className="mt-6 border-cap-blue/20 bg-cap-mist/50">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-cap-blue shadow-sm">
                <Sparkles className="h-5 w-5" />
              </span>
              <div>
                <p className="text-sm font-semibold text-cap-navy">Just here to look around?</p>
                <p className="mt-1 text-sm text-cap-slate leading-relaxed">
                  Use the demo account - it already has a plan, logged progress and a
                  history to explore. No need to type anything.
                </p>
                <dl className="mt-3 space-y-1 text-xs text-cap-slate">
                  <div className="flex gap-2">
                    <dt className="font-semibold text-cap-navy">Email</dt>
                    <dd className="font-mono">{DEMO_EMAIL}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="font-semibold text-cap-navy">Password</dt>
                    <dd className="font-mono">{DEMO_PASSWORD}</dd>
                  </div>
                </dl>
                <Button variant="secondary" className="mt-4" onClick={fillDemoAndSignIn} disabled={submitting}>
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
                  Continue with the demo account
                </Button>
              </div>
            </div>
          </BentoCard>
        </div>

        <BentoCard>
          <div className="flex rounded-xl border border-cap-line bg-cap-mist/40 p-1 text-sm font-medium">
            <button
              type="button"
              onClick={() => { setMode("login"); setError(null); }}
              className={`flex-1 rounded-lg py-2 transition-colors ${mode === "login" ? "bg-white text-cap-navy shadow-sm" : "text-cap-slate"}`}
            >
              Log in
            </button>
            <button
              type="button"
              onClick={() => { setMode("register"); setError(null); }}
              className={`flex-1 rounded-lg py-2 transition-colors ${mode === "register" ? "bg-white text-cap-navy shadow-sm" : "text-cap-slate"}`}
            >
              Create account
            </button>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            {mode === "register" ? (
              <Field label="What should we call you?">
                <input
                  className={inputClass}
                  value={form.name}
                  onChange={(event) => update("name", event.target.value)}
                  placeholder="Your name"
                  required
                />
              </Field>
            ) : null}
            <Field label="Email">
              <input
                type="email"
                className={inputClass}
                value={form.email}
                onChange={(event) => update("email", event.target.value)}
                placeholder="you@example.com"
                required
              />
            </Field>
            <Field label="Password">
              <input
                type="password"
                className={inputClass}
                value={form.password}
                onChange={(event) => update("password", event.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
                minLength={mode === "register" ? 8 : undefined}
                required
              />
            </Field>

            {error ? (
              <p className="rounded-xl border border-signal-bad/30 bg-signal-bad/10 px-4 py-3 text-sm text-signal-bad">
                {error}
              </p>
            ) : null}

            <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : mode === "login" ? (
                <LogIn className="h-4 w-4" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {submitting
                ? "One moment..."
                : mode === "login"
                  ? "Log in"
                  : "Create my account"}
              {!submitting ? <ArrowRight className="h-4 w-4" /> : null}
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-cap-slate">
            {mode === "login" ? "New to SkillSync AI? " : "Already have an account? "}
            <button
              type="button"
              onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
              className="font-semibold text-cap-blue hover:underline"
            >
              {mode === "login" ? "Create one" : "Log in instead"}
            </button>
          </p>
        </BentoCard>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
