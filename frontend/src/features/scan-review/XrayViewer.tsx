import { useCallback, useEffect, useRef, useState } from "react";
import type { Finding, MissingTooth, ReviewStatus } from "../../lib/types";

const STROKE: Record<ReviewStatus, string> = { pending: "#f59e0b", confirmed: "#10b981", modified: "#0ea5e9", rejected: "#94a3b8" };
const MISSING_STROKE = "#38bdf8";
const MIN_ZOOM = 1;
const MAX_ZOOM = 6;

const clamp = (value: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, value));

/**
 * The radiograph with one box per finding. Boxes are in image pixels, so the SVG uses the image's
 * own coordinate system (viewBox) and scales with it. Size comes from the scan record, else from the image.
 *
 * `missing` is the advisory missing-teeth layer: dashed boxes drawn behind the findings, never
 * clickable, so a dentist cannot mistake them for reviewed disease findings.
 *
 * Wheel zooms around the cursor, drag pans, double-click (or Reset) returns to fit. The transform is
 * applied to the image and the overlay together, so boxes stay registered at every zoom level.
 */
export function XrayViewer({ src, width, height, findings, missing = [], selectedId, onSelect }: {
  src: string;
  width: number | null;
  height: number | null;
  findings: Finding[];
  missing?: MissingTooth[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const [failed, setFailed] = useState(false);
  // Panoramas are several MB; until one arrives, boxes on a black panel look like a broken page.
  const [loaded, setLoaded] = useState(false);
  const [view, setView] = useState({ zoom: 1, x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; panX: number; panY: number; moved: boolean } | null>(null);
  const dragged = useRef(false);
  const w = width || natural?.w;
  const h = height || natural?.h;

  const reset = useCallback(() => setView({ zoom: 1, x: 0, y: 0 }), []);

  const zoomAt = useCallback((clientX: number, clientY: number, factor: number) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = clientX - rect.left;
    const py = clientY - rect.top;
    setView((v) => {
      const zoom = clamp(v.zoom * factor, MIN_ZOOM, MAX_ZOOM);
      if (zoom === v.zoom) return v;
      const k = zoom / v.zoom;
      return { zoom, x: px - k * (px - v.x), y: py - k * (py - v.y) };
    });
  }, []);

  const zoomCenter = (factor: number) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
  };

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      zoomAt(event.clientX, event.clientY, event.deltaY < 0 ? 1.15 : 1 / 1.15);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoomAt]);

  if (failed) return <div className="flex aspect-[2/1] items-center justify-center rounded-lg bg-slate-900 text-sm text-slate-300">Image could not be loaded.</div>;

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    drag.current = { x: event.clientX, y: event.clientY, panX: view.x, panY: view.y, moved: false };
    dragged.current = false;
    // No pointer capture yet: browsers retarget the following click to the capturing element,
    // which would swallow clicks on the finding boxes. Capture only once a drag really starts.
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d) return;
    const dx = event.clientX - d.x;
    const dy = event.clientY - d.y;
    if (!d.moved && Math.abs(dx) + Math.abs(dy) > 4) {
      d.moved = true;
      event.currentTarget.setPointerCapture(event.pointerId);   // keep panning outside the viewer
    }
    if (!d.moved) return;
    dragged.current = true;
    setView((v) => ({ ...v, x: d.panX + dx, y: d.panY + dy }));
  };

  const endDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!drag.current) return;
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    // The click event fires immediately after pointerup; clear the flag after it.
    window.setTimeout(() => { dragged.current = false; }, 0);
    setView((v) => (v.zoom === 1 ? { zoom: 1, x: 0, y: 0 } : v));
  };

  return (
    <div
      ref={containerRef}
      className="relative touch-none overflow-hidden rounded-lg bg-black"
      style={{ cursor: view.zoom > 1 ? "grab" : "default" }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onDoubleClick={reset}
      data-testid="viewer"
    >
      <div
        className="relative"
        style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})`, transformOrigin: "0 0", willChange: "transform" }}
        data-testid="viewport"
      >
        <img src={src} alt="Panoramic radiograph" className="block w-full select-none" draggable={false}
          style={w && h && !loaded ? { aspectRatio: `${w} / ${h}` } : undefined}
          onLoad={(e) => { setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight }); setLoaded(true); }}
          onError={() => setFailed(true)} />
        {!loaded && (
          <div className="absolute inset-0 flex min-h-40 items-center justify-center text-sm text-slate-300" role="status">
            Loading radiograph…
          </div>
        )}
        {loaded && w && h && (
          <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full" data-testid="overlay">
            {missing.map((m) => {
              if (!m.box) return null;
              const [x1, y1, x2, y2] = m.box;
              const sw = Math.max(w, h) / 500;
              return (
                <g key={`missing-${m.tooth_fdi}`} className="pointer-events-none" data-testid="missing-tooth">
                  <rect x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="rgba(56,189,248,0.10)"
                    stroke={MISSING_STROKE} strokeWidth={sw} strokeDasharray={`${sw * 3} ${sw * 2}`} />
                  <text x={x1} y={Math.max(y1 - sw * 2, sw * 9)} fill={MISSING_STROKE} fontSize={sw * 9} fontWeight="bold">
                    Missing {m.tooth_fdi}
                  </text>
                </g>
              );
            })}
            {findings.map((f) => {
              const [x1, y1, x2, y2] = f.box;
              const selected = f.id === selectedId;
              const sw = Math.max(w, h) / (selected ? 260 : 400);
              return (
                <g key={f.id} onClick={() => { if (!dragged.current) onSelect(f.id); }} className="cursor-pointer">
                  <rect x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill={selected ? "rgba(255,255,255,0.12)" : "transparent"}
                    stroke={STROKE[f.review_status]} strokeWidth={sw} strokeDasharray={f.review_status === "rejected" ? `${sw * 3} ${sw * 2}` : undefined} />
                  <text x={x1} y={Math.max(y1 - sw * 2, sw * 8)} fill={STROKE[f.review_status]} fontSize={sw * 9} fontWeight="bold">{f.tooth_fdi}</text>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      <div className="absolute right-2 top-2 flex items-center gap-1" onPointerDown={(e) => e.stopPropagation()}>
        <button type="button" aria-label="Zoom in" onClick={() => zoomCenter(1.25)}
          className="rounded bg-black/70 px-2 py-1 text-xs font-medium text-white hover:bg-black/90">+</button>
        <button type="button" aria-label="Zoom out" onClick={() => zoomCenter(1 / 1.25)}
          className="rounded bg-black/70 px-2 py-1 text-xs font-medium text-white hover:bg-black/90">−</button>
        <button type="button" aria-label="Reset zoom" onClick={reset}
          className="rounded bg-black/70 px-2 py-1 text-xs font-medium text-white hover:bg-black/90">Reset</button>
      </div>
      <p className="pointer-events-none absolute bottom-2 left-2 rounded bg-black/60 px-2 py-0.5 text-[11px] text-white">
        Scroll to zoom · drag to pan · double-click to reset
      </p>
    </div>
  );
}
