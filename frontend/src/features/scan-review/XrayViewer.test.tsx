import { fireEvent, render, screen } from "@testing-library/react";
import { XrayViewer } from "./XrayViewer";
import type { Finding } from "../../lib/types";

const finding = (id: string, status: Finding["review_status"]): Finding => ({
  id, scan_id: "s", patient_id: "p", quadrant: 3, tooth_id: 6, tooth_fdi: "36", disease: "Caries", disease_confidence: 0.8,
  box: [10, 20, 60, 90], review_status: status, confirmed_disease: null, dentist_notes: null,
});

test("boxes are drawn in image pixel coordinates and are clickable", () => {
  const onSelect = vi.fn();
  render(<XrayViewer src="x.png" width={700} height={350} findings={[finding("a", "pending"), finding("b", "rejected")]} selectedId="a" onSelect={onSelect} />);
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
