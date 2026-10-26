// ¿Hay conexión? Para avisar y deshabilitar acciones que necesitan la red (pagar, aceptar, avanzar).
import { useSyncExternalStore } from "react";

export function suscribirConexion(aviso: () => void) {
  window.addEventListener("online", aviso);
  window.addEventListener("offline", aviso);
  return () => {
    window.removeEventListener("online", aviso);
    window.removeEventListener("offline", aviso);
  };
}

export const hayConexion = () => navigator.onLine;

export function useEnLinea(): boolean {
  return useSyncExternalStore(suscribirConexion, hayConexion, () => true);
}
