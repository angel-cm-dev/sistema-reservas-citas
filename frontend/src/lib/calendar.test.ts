import { groupByDay, positionEvent } from "./calendar";

const RANGE = { startHour: 8, endHour: 18 }; // 600 minutos visibles

describe("positionEvent", () => {
  it("posiciona un evento dentro del rango", () => {
    const pos = positionEvent("2026-11-03T09:00:00", "2026-11-03T10:00:00", RANGE);
    expect(pos!.top).toBeCloseTo(10);
    expect(pos!.height).toBeCloseTo(10);
  });

  it("recorta eventos que exceden el rango visible", () => {
    const pos = positionEvent("2026-11-03T17:30:00", "2026-11-03T19:00:00", RANGE);
    expect(pos!.top + pos!.height).toBeCloseTo(100);
  });

  it("ignora eventos completamente fuera del rango", () => {
    expect(positionEvent("2026-11-03T06:00:00", "2026-11-03T07:00:00", RANGE)).toBeNull();
  });
});

describe("groupByDay", () => {
  it("agrupa por fecha de inicio", () => {
    const g = groupByDay([
      { id: 1, start_at: "2026-11-03T09:00:00" },
      { id: 2, start_at: "2026-11-03T15:00:00" },
      { id: 3, start_at: "2026-11-04T09:00:00" },
    ]);
    expect(Object.keys(g)).toEqual(["2026-11-03", "2026-11-04"]);
    expect(g["2026-11-03"]).toHaveLength(2);
  });
});
