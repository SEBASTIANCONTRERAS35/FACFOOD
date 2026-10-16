// Solo en desarrollo: entra como cualquier usuario de ejemplo sin login
// (comprador, vendedor o repartidor). Usa el encabezado X-Usuario-Id.
import { useEffect, useState } from "react";
import { api, sesion } from "../api/client";

type UsuarioPrueba = { id: number; nombre: string; rol: string };

export function SelectorUsuarioPrueba() {
  const [usuarios, setUsuarios] = useState<UsuarioPrueba[]>([]);
  const [abierto, setAbierto] = useState(false);
  const actual = sesion.usuarioPrueba();

  useEffect(() => {
    api<UsuarioPrueba[]>("/dev/usuarios").then(setUsuarios).catch(() => setUsuarios([]));
  }, []);

  if (!usuarios.length) return null;

  const elegir = (id: number | null) => {
    sesion.guardarToken(null);
    sesion.guardarUsuarioPrueba(id);
    window.location.reload();
  };

  return (
    <div className="selector-prueba">
      {abierto && (
        <ul>
          {usuarios.map((u) => (
            <li key={u.id}>
              <button type="button" onClick={() => elegir(u.id)} aria-pressed={String(u.id) === actual}>
                {u.nombre} · {u.rol}
              </button>
            </li>
          ))}
          <li>
            <button type="button" onClick={() => elegir(null)}>Salir del modo prueba</button>
          </li>
        </ul>
      )}
      <button type="button" className="selector-prueba__abrir" onClick={() => setAbierto(!abierto)}>
        DEV {actual ? `· #${actual}` : ""}
      </button>
    </div>
  );
}
