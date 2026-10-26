// Tarjeta "Instalar FACFOOD" (Perfil y primera visita a Explorar).
import { useState } from "react";
import { Boton } from "../components";
import { instalar, useInstalacion } from "./instalacion";
import "./pwa.css";

const CLAVE_DESCARTADO = "facfood.pwa.descartado";

export function InstalarApp({ descartable = false }: { descartable?: boolean }) {
  const estado = useInstalacion();
  const [descartado, setDescartado] = useState(() => descartable && localStorage.getItem(CLAVE_DESCARTADO) === "1");

  if (descartado || estado === "instalada" || estado === "no-disponible") return null;

  const descartar = () => {
    localStorage.setItem(CLAVE_DESCARTADO, "1");
    setDescartado(true);
  };

  return (
    <section className="instalar-app" aria-label="Instalar FACFOOD">
      <img src="/pwa-64x64.png" alt="" width={44} height={44} />
      <div className="instalar-app__texto">
        <strong>Instala FACFOOD</strong>
        {estado === "ios" ? (
          <span>En Safari toca <b>Compartir</b> y luego <b>Agregar a inicio</b>.</span>
        ) : (
          <span>Ábrela desde tu pantalla de inicio, a pantalla completa.</span>
        )}
      </div>
      <div className="instalar-app__acciones">
        {estado === "disponible" && <Boton onClick={() => void instalar()}>Instalar</Boton>}
        {descartable && (
          <button type="button" className="instalar-app__cerrar" onClick={descartar} aria-label="No mostrar de nuevo">
            ×
          </button>
        )}
      </div>
    </section>
  );
}
