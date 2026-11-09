import { canSubmit, requirementFor, statusAfterModify, worst } from "./gate";
import type { SafetyWarning } from "./types";

const r18: SafetyWarning = { code: "FIRST_LINE_EXCLUDED", rule_id: "R-18", severity: "warning", drug: "Clindamycin", message: "", source: "" };

test("requirement follows the backend status", () => {
  expect(requirementFor("clear")).toBeNull();
  expect(requirementFor("warning")).toBe("acknowledge");
  expect(requirementFor("contraindicated")).toBe("override");
});

test("submit needs the acknowledgement or a non-blank reason", () => {
  expect(canSubmit(null, false, "")).toBe(true);
  expect(canSubmit("acknowledge", false, "")).toBe(false);
  expect(canSubmit("acknowledge", true, "")).toBe(true);
  expect(canSubmit("override", true, "   ")).toBe(false);
  expect(canSubmit("override", false, "tolerated before")).toBe(true);
});

test("worst picks the most severe status", () => {
  expect(worst("clear", "warning", "clear")).toBe("warning");
  expect(worst("warning", "contraindicated")).toBe("contraindicated");
  expect(worst()).toBe("clear");
});

test("the R-18 substitution notice survives a modify only when the drug is unchanged", () => {
  expect(statusAfterModify("clear", "Clindamycin", "clindamycin ", [r18])).toBe("warning");
  expect(statusAfterModify("clear", "Clindamycin", "Azithromycin", [r18])).toBe("clear");
  expect(statusAfterModify("contraindicated", "Clindamycin", "Clindamycin", [r18])).toBe("contraindicated");
  expect(statusAfterModify("clear", "Amoxicillin", "Amoxicillin", [])).toBe("clear");
});
