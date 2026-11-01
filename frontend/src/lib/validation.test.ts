import { email, hasErrors, minLength, numberBetween, required, strongPassword, validate } from "./validation";

interface F {
  name: string;
  mail: string;
  price: string;
  pass: string;
}

const schema = {
  name: [required<F>(), minLength<F>(3)],
  mail: [required<F>(), email<F>()],
  price: [numberBetween<F>(0, 100)],
  pass: [strongPassword<F>()],
};

describe("validate", () => {
  it("devuelve el primer error por campo", () => {
    const e = validate({ name: "", mail: "x", price: "500", pass: "abc" }, schema);
    expect(e).toEqual({
      name: "Campo obligatorio",
      mail: "Correo inválido",
      price: "Debe estar entre 0 y 100",
      pass: "Mínimo 8 caracteres",
    });
    expect(hasErrors(e)).toBe(true);
  });

  it("acepta datos válidos", () => {
    const e = validate({ name: "Fisioterapia", mail: "a@demo.pe", price: "80", pass: "Clave1234" }, schema);
    expect(hasErrors(e)).toBe(false);
  });

  it("exige letras y números en la contraseña", () => {
    expect(validate({ name: "Ana", mail: "a@b.pe", price: "1", pass: "solotexto" }, schema).pass).toBe(
      "Debe contener letras y números",
    );
  });
});
