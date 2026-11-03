// Cliente HTTP de la API. Lo usan todas las vistas.
// Autenticación: token JWT si hay sesión; si no, en desarrollo, el usuario de prueba elegido.

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const CLAVE_TOKEN = "facfood.token";
const CLAVE_USUARIO_PRUEBA = "facfood.usuarioPrueba";

export class ApiError extends Error {
  constructor(
    public status: number,
    mensaje: string,
    public codigo?: string,
    /** Errores de validación por campo (422 de FastAPI): { correo: "Escribe un correo válido" } */
    public campos: Record<string, string> = {},
  ) {
    super(mensaje);
  }
}

export const sesion = {
  token: () => localStorage.getItem(CLAVE_TOKEN),
  guardarToken: (t: string | null) => (t ? localStorage.setItem(CLAVE_TOKEN, t) : localStorage.removeItem(CLAVE_TOKEN)),
  usuarioPrueba: () => localStorage.getItem(CLAVE_USUARIO_PRUEBA),
  guardarUsuarioPrueba: (id: number | null) =>
    id ? localStorage.setItem(CLAVE_USUARIO_PRUEBA, String(id)) : localStorage.removeItem(CLAVE_USUARIO_PRUEBA),
};

type Opciones = { method?: string; body?: unknown; signal?: AbortSignal };

export async function api<T>(ruta: string, { method = "GET", body, signal }: Opciones = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = sesion.token();
  const prueba = sesion.usuarioPrueba();
  if (token) headers.Authorization = `Bearer ${token}`;
  else if (prueba) headers["X-Usuario-Id"] = prueba;

  let respuesta: Response;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    if (!navigator.onLine) throw new ApiError(0, "Sin conexión. Revisa tu internet e intenta de nuevo.");
    throw new ApiError(0, "No hay conexión con el servidor. ¿Está corriendo la API?");
  }

  const datos = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new ApiError(respuesta.status, mensajeDeError(datos), datos?.codigo, erroresPorCampo(datos));
  return datos as T;
}

// Errores RFC 7807: {type, title, status, detail, instance, codigo, invalid_params?: [{name, reason}]}
type Problema = { detail?: unknown; codigo?: string; invalid_params?: { name?: string; reason?: string }[] };

function erroresPorCampo(datos: unknown): Record<string, string> {
  const campos: Record<string, string> = {};
  for (const p of (datos as Problema | null)?.invalid_params ?? []) {
    if (p.name && p.reason) campos[p.name] = p.reason;
  }
  return campos;
}

function mensajeDeError(datos: unknown): string {
  const detalle = (datos as Problema | null)?.detail;
  return typeof detalle === "string" && detalle ? detalle : "Algo salió mal. Intenta de nuevo.";
}
