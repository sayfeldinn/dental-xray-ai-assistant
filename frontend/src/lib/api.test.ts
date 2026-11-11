import { ApiError, api, configureAuth } from "./api";

const reply = (body: unknown, status: number) => new Response(JSON.stringify(body), { status });

afterEach(() => {
  configureAuth(async () => null, () => {});
  vi.unstubAllGlobals();
});

test("non-2xx responses become ApiError carrying the backend detail", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply({ detail: "needs override_reason" }, 422)));
  await expect(api.getScan("s1")).rejects.toMatchObject({ status: 422, message: "needs override_reason" });
});

test("a FastAPI validation list is flattened into one message", async () => {
  const detail = [{ loc: ["body", "tooth_fdi"], msg: "bad code" }, { loc: ["body"], msg: "whole body" }];
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply({ detail }, 422)));
  await expect(api.getScan("s1")).rejects.toMatchObject({ message: "bad code · whole body" });
});

test("a non-JSON error body falls back to the status", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>bad gateway</html>", { status: 502 })));
  const err = await api.getScan("s1").catch((e) => e);
  expect(err).toMatchObject({ status: 502, message: "Request failed with status 502" });
});

test("a network failure is reported as an unreachable backend", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
  const err = await api.getScan("s1").catch((e) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err.status).toBe(0);
});

test("requests carry the session token and a 401 signs the user out", async () => {
  const unauthorized = vi.fn();
  configureAuth(async () => "tok-123", unauthorized);
  const fetchMock = vi.fn().mockResolvedValue(reply({ detail: "Session expired" }, 401));
  vi.stubGlobal("fetch", fetchMock);
  await expect(api.listPatients()).rejects.toMatchObject({ status: 401 });
  expect((fetchMock.mock.calls[0][1].headers as Headers).get("Authorization")).toBe("Bearer tok-123");
  expect(unauthorized).toHaveBeenCalledOnce();
});
