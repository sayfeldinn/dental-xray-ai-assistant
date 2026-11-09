import { ApiError, api, parseDetail } from "./api";

test("parseDetail flattens FastAPI string and validation-list details", () => {
  expect(parseDetail({ detail: "Prescription already accepted" }, "x")).toBe("Prescription already accepted");
  expect(parseDetail({ detail: [{ loc: ["body", "tooth_fdi"], msg: "bad code" }, { loc: ["body"], msg: "whole body" }] }, "x"))
    .toBe("tooth_fdi: bad code; whole body");
  expect(parseDetail(null, "fallback")).toBe("fallback");
});

test("non-2xx responses become ApiError with the backend detail", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "needs override_reason" }), { status: 422 })));
  await expect(api.getScan("s1")).rejects.toMatchObject({ status: 422, detail: "needs override_reason" });
  vi.unstubAllGlobals();
});

test("a network failure is reported as unreachable backend", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
  const err = await api.getScan("s1").catch((e) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err.status).toBe(0);
  vi.unstubAllGlobals();
});

test("requests carry the session token and a 401 signs the user out", async () => {
  const { configureAuth } = await import("./api");
  const unauthorized = vi.fn();
  configureAuth(async () => "tok-123", unauthorized);
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Session expired" }), { status: 401 }));
  vi.stubGlobal("fetch", fetchMock);
  await expect(api.listPatients()).rejects.toMatchObject({ status: 401 });
  expect((fetchMock.mock.calls[0][1].headers as Headers).get("Authorization")).toBe("Bearer tok-123");
  expect(unauthorized).toHaveBeenCalledOnce();
  configureAuth(async () => null, () => {});
  vi.unstubAllGlobals();
});
