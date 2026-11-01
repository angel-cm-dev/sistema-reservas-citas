import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { navFor } from "./Layout";
import { scheduleErrors } from "./ScheduleEditor";
import { Pagination } from "./ui/Pagination";
import { StatusBadge } from "./ui/StatusBadge";

describe("Pagination", () => {
  it("muestra el resumen y deshabilita el botón anterior en la primera página", async () => {
    const onChange = vi.fn();
    render(<Pagination page={1} pages={3} total={25} onChange={onChange} />);
    expect(screen.getByText(/25 registros · Página 1 de 3/)).toBeInTheDocument();
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();
    await userEvent.click(screen.getByLabelText("Página siguiente"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("no se renderiza sin registros", () => {
    const { container } = render(<Pagination page={1} pages={0} total={0} onChange={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("StatusBadge", () => {
  it("traduce el estado", () => {
    render(<StatusBadge status="no_asistio" />);
    expect(screen.getByText("No asistió")).toBeInTheDocument();
  });
});

describe("navFor", () => {
  it("filtra el menú por rol", () => {
    expect(navFor("cliente").map((i) => i.to)).toEqual(["/citas", "/reservar"]);
    expect(navFor("profesional").map((i) => i.to)).toContain("/mi-horario");
    expect(navFor("admin").map((i) => i.to)).toContain("/recordatorios");
  });
});

describe("scheduleErrors", () => {
  it("detecta bloques cruzados en el mismo día", () => {
    expect(
      scheduleErrors([
        { weekday: 0, start_time: "09:00", end_time: "13:00" },
        { weekday: 0, start_time: "12:00", end_time: "15:00" },
      ]),
    ).toMatch(/se cruzan/);
  });

  it("acepta bloques consecutivos y en días distintos", () => {
    expect(
      scheduleErrors([
        { weekday: 0, start_time: "09:00", end_time: "13:00" },
        { weekday: 0, start_time: "13:00", end_time: "15:00" },
        { weekday: 1, start_time: "10:00", end_time: "12:00" },
      ]),
    ).toBeNull();
  });

  it("rechaza fin anterior al inicio", () => {
    expect(scheduleErrors([{ weekday: 2, start_time: "12:00", end_time: "09:00" }])).toMatch(/posterior/);
  });
});
