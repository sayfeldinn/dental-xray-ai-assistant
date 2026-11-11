import { fireEvent, render, screen } from "@testing-library/react";

const loadImage = () => fireEvent.load(screen.getByAltText("Panoramic radiograph"));
import { XrayViewer } from "./XrayViewer";
import type { Finding } from "../../lib/types";

const finding = (id: string, status: Finding["review_status"]): Finding => ({
  id, scan_id: "s", patient_id: "p", quadrant: 3, tooth_id: 6, tooth_fdi: "36", disease: "Caries", disease_confidence: 0.8,
  box: [10, 20, 60, 90], review_status: status, confirmed_disease: null, dentist_notes: null,
});

test("boxes are drawn in image pixel coordinates and are clickable", () => {
  const onSelect = vi.fn();
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending"), finding("b", "rejected")]} selectedId="a" onSelect={onSelect} />);
  loadImage();
  const svg = screen.getByTestId("overlay");
  expect(svg.getAttribute("viewBox")).toBe("0 0 700 350");
  const rects = svg.querySelectorAll("rect");
  expect(rects).toHaveLength(2);
  expect(rects[0].getAttribute("width")).toBe("50");
  expect(rects[1].getAttribute("stroke-dasharray")).toBeTruthy();   // rejected = dashed
  fireEvent.click(rects[1]);
  expect(onSelect).toHaveBeenCalledWith("b");
});

test("without stored dimensions the overlay waits for the image", () => {
  render(<XrayViewer src="x.png" width={null} height={null} findings={[finding("a", "pending")]} selectedId={null} onSelect={() => {}} />);
  expect(screen.queryByTestId("overlay")).toBeNull();
});

test("missing teeth are dashed advisory boxes that do not capture clicks", () => {
  const onSelect = vi.fn();
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending")]}
    missing={[{ quadrant: 4, tooth_id: 6, tooth: "Tooth_6", tooth_fdi: "46", confidence: 0.8, bounded_by: ["45", "47"], gap_probability: 0.93, box: [100, 100, 140, 160] }]}
    selectedId={null} onSelect={onSelect} />);
  loadImage();
  const groups = screen.getAllByTestId("missing-tooth");
  expect(groups).toHaveLength(1);
  const rect = groups[0].querySelector("rect")!;
  expect(rect.getAttribute("stroke-dasharray")).toBeTruthy();
  expect(screen.getByText("Missing 46")).toBeTruthy();
  fireEvent.click(rect);
  expect(onSelect).not.toHaveBeenCalled();
});

test("zoom controls scale the viewport and reset returns to fit", () => {
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending")]} selectedId={null} onSelect={() => {}} />);
  const viewport = screen.getByTestId("viewport");
  fireEvent.click(screen.getByLabelText("Zoom in"));
  expect(viewport.style.transform).toContain("scale(1.25)");
  fireEvent.click(screen.getByLabelText("Reset zoom"));
  expect(viewport.style.transform).toContain("scale(1)");
});

test("a loading placeholder replaces the boxes until the radiograph arrives", () => {
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending")]} selectedId={null} onSelect={() => {}} />);
  expect(screen.getByRole("status").textContent).toContain("Loading radiograph");
  expect(screen.queryByTestId("overlay")).toBeNull();
  loadImage();
  expect(screen.queryByRole("status")).toBeNull();
  expect(screen.getByTestId("overlay")).toBeTruthy();
});

test("pressing on a box does not capture the pointer, so the click still reaches the box", () => {
  // Browsers retarget a click to whichever element holds pointer capture; capturing on
  // pointerdown made every box click land on the viewer instead (seen in a real browser).
  const onSelect = vi.fn();
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending")]} selectedId={null} onSelect={onSelect} />);
  loadImage();
  const viewer = screen.getByTestId("viewer");
  const capture = vi.fn();
  viewer.setPointerCapture = capture;
  const rect = screen.getByTestId("overlay").querySelector("rect")!;
  fireEvent.pointerDown(rect, { button: 0, pointerId: 1, clientX: 20, clientY: 30 });
  fireEvent.pointerUp(rect, { button: 0, pointerId: 1, clientX: 20, clientY: 30 });
  fireEvent.click(rect);
  expect(capture).not.toHaveBeenCalled();
  expect(onSelect).toHaveBeenCalledWith("a");
});
