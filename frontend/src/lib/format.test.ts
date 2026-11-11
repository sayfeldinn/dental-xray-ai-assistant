import { ageFrom, splitList, toothName } from "./format";

afterEach(() => vi.useRealTimers());

test("FDI codes read as tooth names", () => {
  expect(toothName("36")).toBe("lower left first molar");
  expect(toothName("18")).toBe("upper right third molar");
  expect(toothName("99")).toBe("");
});

test("age counts completed years", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date(2026, 9, 20));
  expect(ageFrom("2000-10-21")).toBe(25);
  expect(ageFrom("2000-10-20")).toBe(26);
});

test("splitList trims and drops blanks", () => {
  expect(splitList(" penicillin, ,sulfa\nlatex ")).toEqual(["penicillin", "sulfa", "latex"]);
});
