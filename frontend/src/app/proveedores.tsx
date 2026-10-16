// Contextos globales (sesión, carrito). Dueño: Sebastián.
import type { ReactNode } from "react";
import { ProveedorSesion } from "../features/cuenta/sesion";

export function Proveedores({ children }: { children: ReactNode }) {
  return <ProveedorSesion>{children}</ProveedorSesion>;
}
