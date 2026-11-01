import { formatDuration, formatMoney, formatTime } from "./format";

describe("format", () => {
  it("formatea soles peruanos", () => {
    expect(formatMoney("90.00")).toMatch(/S\/\s?90\.00/);
  });
  it("formatea duraciones", () => {
    expect(formatDuration(45)).toBe("45 min");
    expect(formatDuration(60)).toBe("1 h");
    expect(formatDuration(90)).toBe("1 h 30 min");
  });
  it("extrae la hora HH:mm", () => {
    expect(formatTime("2026-11-03T09:15:00")).toBe("09:15");
  });
});
