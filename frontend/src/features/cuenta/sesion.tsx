// Sesión del usuario: quién está dentro, login, registro y cierre de sesión.
import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, sesion } from "../../api/client";

export type Usuario = {
  id: number;
  nombre: string;
  correo: string;
  rol: "comprador" | "vendedor" | "repartidor";
  pedidos_completados: number;
  nivel_lealtad: "bronce" | "plata" | "oro";
  puede_vender: boolean;
};

export type DatosRegistro = {
  nombre: string;
  credencial_unam: string;
  correo: string;
  password: string;
  consentimiento_datos: boolean;
};

type RespuestaSesion = { access_token: string; usuario: Usuario };

type ContextoSesion = {
  usuario: Usuario | null;
  cargando: boolean;
  iniciarSesion: (correo: string, password: string) => Promise<Usuario>;
  registrarse: (datos: DatosRegistro) => Promise<Usuario>;
  cerrarSesion: () => void;
  recargar: () => Promise<void>;
};

const Contexto = createContext<ContextoSesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const recargar = useCallback(async () => {
    if (!sesion.token() && !sesion.usuarioPrueba()) {
      setUsuario(null);
      return;
    }
    try {
      setUsuario(await api<Usuario>("/usuarios/me"));
    } catch {
      sesion.guardarToken(null);
      setUsuario(null);
    }
  }, []);

  useEffect(() => {
    recargar().finally(() => setCargando(false));
  }, [recargar]);

  const entrar = (r: RespuestaSesion) => {
    sesion.guardarUsuarioPrueba(null);
    sesion.guardarToken(r.access_token);
    setUsuario(r.usuario);
    return r.usuario;
  };

  const valor: ContextoSesion = {
    usuario,
    cargando,
    recargar,
    iniciarSesion: async (correo, password) =>
      entrar(await api<RespuestaSesion>("/auth/login", { method: "POST", body: { correo, password } })),
    registrarse: async (datos) => entrar(await api<RespuestaSesion>("/auth/registro", { method: "POST", body: datos })),
    cerrarSesion: () => {
      sesion.guardarToken(null);
      sesion.guardarUsuarioPrueba(null);
      setUsuario(null);
    },
  };

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion() {
  const c = useContext(Contexto);
  if (!c) throw new Error("useSesion debe usarse dentro de <ProveedorSesion>");
  return c;
}

/** Envuelve una vista que requiere sesión; si no hay, manda a /login y regresa después. */
export function RequiereSesion({ children }: { children: ReactNode }) {
  const { usuario, cargando } = useSesion();
  const ubicacion = useLocation();
  if (cargando) return null;
  if (!usuario) return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  return <>{children}</>;
}
