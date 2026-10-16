import { describe, expect, it } from "vitest";
import { piezas, reducir, subtotalCentavos, VACIO } from "./carrito";

const DON_MEMO = { id: 1, nombre: "Tacos Don Memo" };
const PASTOR = { id: 1, nombre: "Taco de pastor", precio: "18.00" };
const QUESADILLA = { id: 3, nombre: "Quesadilla de queso", precio: "30.00" };

describe("carrito", () => {
  it("suma piezas y subtotal en centavos (caso de la pantalla 03)", () => {
    let c = reducir(VACIO, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    c = reducir(c, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    c = reducir(c, { tipo: "agregar", punto: DON_MEMO, producto: QUESADILLA });
    expect(piezas(c)).toBe(3);
    expect(subtotalCentavos(c)).toBe(6600);
  });

  it("agregar de otro puesto empieza un carrito nuevo", () => {
    let c = reducir(VACIO, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    c = reducir(c, { tipo: "agregar", punto: { id: 2, nombre: "Café" }, producto: { id: 9, nombre: "Café", precio: "22.00" } });
    expect(c.punto?.id).toBe(2);
    expect(c.lineas).toHaveLength(1);
  });

  it("quitar la última pieza vacía el carrito", () => {
    let c = reducir(VACIO, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    c = reducir(c, { tipo: "quitar", producto_id: 1 });
    expect(c).toEqual(VACIO);
  });

  it("cambiar el contenido descarta la orden creada", () => {
    let c = reducir(VACIO, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    c = reducir(c, { tipo: "orden", id: 7 });
    expect(c.ordenId).toBe(7);
    c = reducir(c, { tipo: "agregar", punto: DON_MEMO, producto: PASTOR });
    expect(c.ordenId).toBeNull();
  });
});
