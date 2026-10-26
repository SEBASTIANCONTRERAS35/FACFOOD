// Instalar la PWA: Chrome/Edge/Android disparan `beforeinstallprompt`; Safari en iPhone no,
// ahí se explican los pasos (Compartir → Agregar a inicio).
import { useSyncExternalStore } from "react";

type EventoInstalacion = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: "accepted" | "dismissed" }> };

export type EstadoInstalacion = "instalada" | "disponible" | "ios" | "no-disponible";

let pendiente: EventoInstalacion | null = null;
const avisos = new Set<() => void>();
const avisar = () => avisos.forEach((a) => a());

// Se registra al importar el módulo (desde main.tsx): el evento puede llegar antes de que React monte.
if (typeof window !== "undefined") {
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault(); // la mostramos nosotros, con nuestro botón
    pendiente = e as EventoInstalacion;
    avisar();
  });
  window.addEventListener("appinstalled", () => {
    pendiente = null;
    avisar();
  });
}

export function esIOS(ua: string): boolean {
  return /iphone|ipad|ipod/i.test(ua);
}

export function esStandalone(): boolean {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches === true ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

export function estadoInstalacion(ua = navigator.userAgent): EstadoInstalacion {
  if (esStandalone()) return "instalada";
  if (pendiente) return "disponible";
  if (esIOS(ua)) return "ios";
  return "no-disponible";
}

export async function instalar(): Promise<boolean> {
  if (!pendiente) return false;
  const evento = pendiente;
  pendiente = null;
  await evento.prompt();
  const { outcome } = await evento.userChoice;
  avisar();
  return outcome === "accepted";
}

function suscribir(aviso: () => void) {
  avisos.add(aviso);
  return () => {
    avisos.delete(aviso);
  };
}

export function useInstalacion(): EstadoInstalacion {
  return useSyncExternalStore(suscribir, () => estadoInstalacion(), () => "no-disponible");
}
