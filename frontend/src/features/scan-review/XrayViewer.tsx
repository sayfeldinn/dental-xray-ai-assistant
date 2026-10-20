import { useState } from "react";
import type { Finding, ReviewStatus } from "../../lib/types";

const STROKE: Record<ReviewStatus, string> = { pending: "#f59e0b", confirmed: "#10b981", modified: "#0ea5e9", rejected: "#94a3b8" };

/**
 * The radiograph with one box per finding. Boxes are in image pixels, so the SVG uses the image's
 * own coordinate system (viewBox) and scales with it. Size comes from the scan record, else from the image.
 */
export function XrayViewer({ src, width, height, findings, selectedId, onSelect }: {
  src: string;
  width: number | null;
  height: number | null;
  findings: Finding[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const [failed, setFailed] = useState(false);
  const w = width || natural?.w;
  const h = height || natural?.h;

  if (failed) return <div className="flex aspect-[2/1] items-center justify-center rounded-lg bg-slate-900 text-sm text-slate-300">Image could not be loaded.</div>;

  return (
    <div className="relative overflow-hidden rounded-lg bg-black">
      <img src={src} alt="Panoramic radiograph" className="block w-full select-none" draggable={false}
        onLoad={(e) => setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
        onError={() => setFailed(true)} />
      {w && h && (
        <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full" data-testid="overlay">
          {findings.map((f) => {
            const [x1, y1, x2, y2] = f.box;
            const selected = f.id === selectedId;
            const sw = Math.max(w, h) / (selected ? 260 : 400);
            return (
              <g key={f.id} onClick={() => onSelect(f.id)} className="cursor-pointer">
                <rect x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill={selected ? "rgba(255,255,255,0.12)" : "transparent"}
                  stroke={STROKE[f.review_status]} strokeWidth={sw} strokeDasharray={f.review_status === "rejected" ? `${sw * 3} ${sw * 2}` : undefined} />
                <text x={x1} y={Math.max(y1 - sw * 2, sw * 8)} fill={STROKE[f.review_status]} fontSize={sw * 9} fontWeight="bold">{f.tooth_fdi}</text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
