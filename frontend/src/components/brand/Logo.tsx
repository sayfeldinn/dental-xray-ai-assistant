/** Tooth mark + wordmark. `tone` adapts it to rose (hero) or light (app header) backgrounds. */
export function Logo({ tone = "brand" }: { tone?: "brand" | "white" }) {
  const fg = tone === "white" ? "#ffffff" : "#DB2550";
  return (
    <span className="inline-flex items-center gap-2">
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
        <rect width="32" height="32" rx="9" fill={fg} />
        <path d="M9 9c3-2 5 0 7 0s4-2 7 0c2 2 1 7-1 10l-2 6c-1 2-2 1-2-1l-1-5c0-1-2-1-2 0l-1 5c0 2-1 3-2 1l-2-6c-2-3-3-8-1-10z"
          fill={tone === "white" ? "#DB2550" : "#ffffff"} />
      </svg>
      <span className="title text-lg" style={{ color: fg }}>DentalAI</span>
    </span>
  );
}
