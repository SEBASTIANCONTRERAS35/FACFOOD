// Sustituto de "virtual:pwa-register/react" para Vitest (el módulo real solo existe en el build).
import { useState } from "react";

export function useRegisterSW() {
  return {
    needRefresh: useState(false),
    offlineReady: useState(false),
    updateServiceWorker: async () => {},
  };
}
