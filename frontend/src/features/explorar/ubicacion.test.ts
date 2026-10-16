import { describe, expect, it } from "vitest";
import { distanciaM, elegirUbicacion, FACULTAD_DE_INGENIERIA } from "./ubicacion";

describe("ubicación", () => {
  it("usa la ubicación real si está dentro de CU", () => {
    expect(elegirUbicacion(19.3335, -99.1858)).toEqual({ lat: 19.3335, lon: -99.1858, real: true });
  });

  it("usa la Facultad de Ingeniería si el usuario está lejos de CU", () => {
    expect(elegirUbicacion(19.4326, -99.1332)).toEqual(FACULTAD_DE_INGENIERIA); // Zócalo
  });

  it("calcula distancias del orden de cientos de metros dentro de CU", () => {
    const d = distanciaM(FACULTAD_DE_INGENIERIA, { lat: 19.332, lon: -99.1832 });
    expect(d).toBeGreaterThan(100);
    expect(d).toBeLessThan(150);
  });
});
