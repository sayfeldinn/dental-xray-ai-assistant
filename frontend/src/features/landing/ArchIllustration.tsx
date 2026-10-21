/**
 * A drawn panoramic radiograph: both dental arches on a dark film, with three AI detection boxes
 * that draw themselves in once (the page's single animation; skipped with reduced motion).
 * Purely illustrative: no patient image is shown on the public page.
 */

const W = 640;
const H = 360;
const N = 16;
const STEP = 35;
const X0 = (W - STEP * (N - 1)) / 2;

/** Occlusal line of a panoramic film: a gentle smile, lowest at the midline. */
const occlusal = (i: number) => {
  const t = (i - (N - 1) / 2) / ((N - 1) / 2);
  return 168 + 26 * (1 - t * t);
};
const toothWidth = (i: number) => {
  const t = Math.abs((i - (N - 1) / 2) / ((N - 1) / 2));
  return 24 + 9 * t ** 1.4;
};
const isMolar = (i: number) => Math.abs(i - (N - 1) / 2) > 4.5;

function Tooth({ i, upper }: { i: number; upper: boolean }) {
  const cx = X0 + i * STEP;
  const w = toothWidth(i);
  const y = occlusal(i);
  const dir = upper ? -1 : 1;
  const crownH = 40;
  const rootL = isMolar(i) ? 52 : 64;
  const crownTop = upper ? y - crownH - 3 : y + 3;
  const rootStart = upper ? crownTop : crownTop + crownH;
  const roots = isMolar(i) ? [cx - w * 0.22, cx + w * 0.22] : [cx];
  return (
    <g>
      {roots.map((rx) => (
        <path key={rx} fill="url(#xr-root)"
          d={`M${rx - w * 0.2} ${rootStart} L${rx + w * 0.2} ${rootStart} L${rx + 2} ${rootStart + dir * rootL} L${rx - 2} ${rootStart + dir * rootL} Z`} />
      ))}
      <rect x={cx - w / 2} y={crownTop} width={w} height={crownH} rx={w * 0.32} fill="url(#xr-enamel)" />
    </g>
  );
}

const BOXES = [
  { upper: false, i: 13, label: "36 · Caries", color: "#f59e0b", delay: 0.4 },
  { upper: true, i: 14, label: "27 · Deep caries", color: "#f59e0b", delay: 0.9 },
  { upper: false, i: 0, label: "48 · Impacted", color: "#34d399", delay: 1.4 },
];

export function ArchIllustration() {
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img"
      aria-label="Illustration of a panoramic dental X-ray with three AI findings marked on teeth 36, 27 and 48">
      <defs>
        <radialGradient id="xr-film" cx="50%" cy="52%" r="65%">
          <stop offset="0%" stopColor="#3b2a30" />
          <stop offset="100%" stopColor="#140b0e" />
        </radialGradient>
        <linearGradient id="xr-enamel" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f6eef0" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#c9b9be" stopOpacity="0.8" />
        </linearGradient>
        <linearGradient id="xr-root" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#d6c7cc" stopOpacity="0.75" />
          <stop offset="100%" stopColor="#d6c7cc" stopOpacity="0.1" />
        </linearGradient>
        <style>{`
          .draw { stroke-dasharray: var(--len); animation: draw 0.9s ease-out both; }
          .tag { animation: show 0.3s ease-out both; }
          @keyframes draw { from { stroke-dashoffset: var(--len); } to { stroke-dashoffset: 0; } }
          @keyframes show { from { opacity: 0; } to { opacity: 1; } }
        `}</style>
      </defs>
      <rect width={W} height={H} rx="28" fill="url(#xr-film)" />
      {/* jaw outlines */}
      <path d={`M30 92 Q320 10 610 92`} stroke="#ffffff" strokeOpacity="0.07" strokeWidth="18" fill="none" />
      <path d={`M40 300 Q320 372 600 300`} stroke="#ffffff" strokeOpacity="0.08" strokeWidth="24" fill="none" />
      {Array.from({ length: N }, (_, i) => <Tooth key={`u${i}`} i={i} upper />)}
      {Array.from({ length: N }, (_, i) => <Tooth key={`l${i}`} i={i} upper={false} />)}
      {BOXES.map((b) => {
        const cx = X0 + b.i * STEP;
        const w = toothWidth(b.i) + 12;
        const y = b.upper ? occlusal(b.i) - 50 : occlusal(b.i) - 4;
        const labelY = b.upper ? y - 9 : y + 70;
        return (
          <g key={b.label}>
            <rect className="draw" style={{ animationDelay: `${b.delay}s`, ["--len" as string]: 2 * (w + 54) }} x={cx - w / 2} y={y} width={w} height={54} rx="7"
              fill="none" stroke={b.color} strokeWidth="2.5" />
            <g className="tag" style={{ animationDelay: `${b.delay + 0.7}s` }}>
              <rect x={cx - 46} y={labelY - 13} width="92" height="19" rx="9.5" fill={b.color} />
              <text x={cx} y={labelY} textAnchor="middle" fontSize="11" fontWeight="700" fill="#24141a" fontFamily="Archivo, sans-serif">{b.label}</text>
            </g>
          </g>
        );
      })}
    </svg>
  );
}
