// Registra el service worker y avisa cuando hay una versión nueva o la app ya funciona sin red.
import { useEffect } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";
import "./pwa.css";

export function Actualizacion() {
  const {
    needRefresh: [hayNueva, setHayNueva],
    offlineReady: [listaSinRed, setListaSinRed],
    updateServiceWorker,
  } = useRegisterSW({ immediate: true });

  useEffect(() => {
    if (!listaSinRed) return;
    const t = setTimeout(() => setListaSinRed(false), 4000);
    return () => clearTimeout(t);
  }, [listaSinRed, setListaSinRed]);

  if (hayNueva) {
    return (
      <div className="aviso-pwa" role="alert">
        <span>Hay una versión nueva de FACFOOD</span>
        <button type="button" onClick={() => void updateServiceWorker(true)}>Actualizar</button>
        <button type="button" aria-label="Después" onClick={() => setHayNueva(false)}>×</button>
      </div>
    );
  }
  if (listaSinRed) {
    return (
      <div className="aviso-pwa" role="status">
        <span>FACFOOD ya funciona sin conexión</span>
      </div>
    );
  }
  return null;
}
