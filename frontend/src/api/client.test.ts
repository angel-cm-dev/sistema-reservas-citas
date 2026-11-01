import { ApiError, buildQuery, request, tokenStore, toApiError } from "./client";

describe("toApiError", () => {
  it("usa detail de ProblemDetails y mapea errores de campo", () => {
    const err = toApiError(422, {
      title: "Datos inválidos",
      status: 422,
      detail: "Revisa los campos indicados.",
      errors: [{ field: "price", message: "debe ser positivo" }],
    });
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toBe("Revisa los campos indicados.");
    expect(err.fieldErrors).toEqual({ price: "debe ser positivo" });
  });

  it("tiene mensaje por defecto para errores 5xx sin cuerpo", () => {
    expect(toApiError(503, null).message).toMatch(/servidor/);
  });
});

describe("buildQuery", () => {
  it("omite valores vacíos", () => {
    expect(buildQuery({ q: "", page: 2, status: undefined, active: true })).toBe("?page=2&active=true");
    expect(buildQuery({})).toBe("");
  });
});

describe("request", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    tokenStore.clear();
  });

  it("envía el token Bearer y devuelve JSON", async () => {
    tokenStore.set("abc");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: 1 }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    await expect(request("GET", "/x")).resolves.toEqual({ ok: 1 });
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });

  it("limpia el token ante un 401", async () => {
    tokenStore.set("expirado");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ title: "No autenticado", status: 401, detail: "El token expiró." }), { status: 401 }),
    );
    await expect(request("GET", "/x")).rejects.toMatchObject({ status: 401, message: "El token expiró." });
    expect(tokenStore.get()).toBeNull();
  });

  it("convierte fallos de red en ApiError legible", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(request("GET", "/x")).rejects.toMatchObject({ status: 0 });
  });
});
