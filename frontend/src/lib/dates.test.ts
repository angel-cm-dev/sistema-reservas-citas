import { addDays, hoursBetween, parseLocal, startOfWeek, toISODate, toLocalISO, weekDays } from "./dates";

describe("dates", () => {
  it("formatea fechas locales sin desfase UTC", () => {
    const d = new Date(2026, 10, 3, 23, 30);
    expect(toISODate(d)).toBe("2026-11-03");
    expect(toLocalISO(d)).toBe("2026-11-03T23:30:00");
  });

  it("parsea strings ISO locales del backend", () => {
    const d = parseLocal("2026-11-03T10:45:00");
    expect([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()]).toEqual([2026, 10, 3, 10, 45]);
    expect(toISODate(parseLocal("2026-12-08"))).toBe("2026-12-08");
  });

  it("calcula el lunes de la semana (incluso desde un domingo)", () => {
    expect(toISODate(startOfWeek(new Date(2026, 10, 1)))).toBe("2026-10-26"); // domingo
    expect(toISODate(startOfWeek(new Date(2026, 10, 4)))).toBe("2026-11-02"); // miércoles
  });

  it("genera los 7 días de la semana y suma días cruzando meses", () => {
    const days = weekDays(new Date(2026, 10, 30)).map(toISODate);
    expect(days[0]).toBe("2026-11-30");
    expect(days[6]).toBe("2026-12-06");
    expect(toISODate(addDays(new Date(2026, 11, 31), 1))).toBe("2027-01-01");
  });

  it("calcula horas entre fechas", () => {
    expect(hoursBetween(parseLocal("2026-11-02T08:00"), parseLocal("2026-11-03T10:00"))).toBe(26);
  });
});
