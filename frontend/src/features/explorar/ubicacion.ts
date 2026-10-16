// Ubicación del usuario. Si no la comparte o está lejos de CU, se usa la Facultad de Ingeniería.
import { useEffect, useState } from "react";

export type Ubicacion = { lat: number; lon: number; real: boolean };

export const FACULTAD_DE_INGENIERIA: Ubicacion = { lat: 19.3311, lon: -99.1839, real: false };
const MAX_DISTANCIA_A_CU_M = 3000;
const CLAVE = "facfood.ubicacion";

export function distanciaM(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLon = (b.lon - a.lon) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371008.8 * Math.asin(Math.sqrt(h));
}

export function elegirUbicacion(lat: number, lon: number): Ubicacion {
  const real = { lat, lon, real: true };
  return distanciaM(real, FACULTAD_DE_INGENIERIA) <= MAX_DISTANCIA_A_CU_M ? real : FACULTAD_DE_INGENIERIA;
}

function guardada(): Ubicacion | null {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE) ?? "null");
  } catch {
    return null;
  }
}

export function useUbicacion(): Ubicacion {
  const [ubicacion, setUbicacion] = useState<Ubicacion>(() => guardada() ?? FACULTAD_DE_INGENIERIA);

  useEffect(() => {
    if (guardada() || !("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const u = elegirUbicacion(p.coords.latitude, p.coords.longitude);
        sessionStorage.setItem(CLAVE, JSON.stringify(u));
        setUbicacion(u);
      },
      () => sessionStorage.setItem(CLAVE, JSON.stringify(FACULTAD_DE_INGENIERIA)),
      { timeout: 5000, maximumAge: 60_000 },
    );
  }, []);

  return ubicacion;
}
