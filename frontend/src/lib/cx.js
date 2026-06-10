/**
 * The two-line stand-in for `clsx` this project doesn't depend on - joins
 * truthy class fragments with a space and drops the rest. Conditional
 * classes show up constantly in a bento layout (active tab, status tone,
 * hover state); this is the smallest thing that makes them readable.
 */
export function cx(...parts) {
  return parts.filter(Boolean).join(" ");
}
