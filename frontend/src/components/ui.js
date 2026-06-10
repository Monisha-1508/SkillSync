"use client";

import Link from "next/link";
import { cx as clsx } from "@/lib/cx";

/**
 * The handful of primitives every screen reaches for - a card with the
 * "bento" treatment already configured in Tailwind, a button in the two
 * brand weights the product actually uses, and a small label/eyebrow pair
 * for section headers. Kept deliberately plain: the brand voice here is
 * "confident and uncluttered", not "look how many components we built".
 */

export function BentoCard({ children, className, as: Tag = "div", ...rest }) {
  return (
    <Tag
      className={clsx(
        "bento-card rounded-bento p-6 md:p-7",
        "hover:shadow-bento-hover transition-shadow",
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function Eyebrow({ children, className }) {
  return (
    <p className={clsx("text-xs font-semibold uppercase tracking-[0.18em] text-cap-vibrant", className)}>
      {children}
    </p>
  );
}

export function SectionHeading({ eyebrow, title, lead, className }) {
  return (
    <div className={clsx("max-w-2xl", className)}>
      {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
      <h2 className="mt-2 font-display text-2xl md:text-3xl font-semibold text-cap-navy">{title}</h2>
      {lead ? <p className="mt-3 text-cap-slate leading-relaxed">{lead}</p> : null}
    </div>
  );
}

const buttonStyles = {
  primary:
    "bg-cap-blue text-white hover:bg-cap-navy shadow-[0_8px_24px_-10px_rgba(0,112,173,0.55)]",
  secondary:
    "bg-white text-cap-blue border border-cap-line hover:border-cap-blue hover:bg-cap-mist",
  ghost: "text-cap-blue hover:bg-cap-mist",
};

export function Button({ children, variant = "primary", className, href, type = "button", ...rest }) {
  const classes = clsx(
    "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5",
    "text-sm font-semibold transition-colors duration-200",
    buttonStyles[variant],
    className,
  );
  if (href) {
    return (
      <Link href={href} className={classes} {...rest}>
        {children}
      </Link>
    );
  }
  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  );
}

export function StatusPill({ status, children }) {
  const tone = {
    good: "bg-signal-good/10 text-signal-good border-signal-good/30",
    warn: "bg-signal-warn/10 text-signal-warn border-signal-warn/30",
    bad: "bg-signal-bad/10 text-signal-bad border-signal-bad/30",
    known: "bg-signal-known/10 text-signal-known border-signal-known/30",
    inferred: "bg-signal-inferred/10 text-signal-inferred border-signal-inferred/30",
    weak: "bg-signal-weak/10 text-signal-weak border-signal-weak/30",
    unknown: "bg-signal-unknown/10 text-signal-unknown border-signal-unknown/30",
  }[status] || "bg-cap-mist text-cap-slate border-cap-line";

  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium", tone)}>
      {children}
    </span>
  );
}
