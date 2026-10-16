// Íconos de línea (mismos trazos que en el Figma). Heredan el color con currentColor.
import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement> & { tam?: number };

function Icono({ tam = 24, children, ...resto }: Props) {
  return (
    <svg
      width={tam}
      height={tam}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...resto}
    >
      {children}
    </svg>
  );
}

export const IconoUbicacion = (p: Props) => (
  <Icono {...p}>
    <path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z" />
    <circle cx="12" cy="10" r="2.5" />
  </Icono>
);
export const IconoPedidos = (p: Props) => (
  <Icono {...p}>
    <rect x="5" y="3" width="14" height="18" rx="2" />
    <path d="M9 8h6M9 12h6M9 16h4" />
  </Icono>
);
export const IconoCupon = (p: Props) => (
  <Icono {...p}>
    <path d="M3 8a2 2 0 0 0 0 4v4h18v-4a2 2 0 0 1 0-4V4H3z" />
    <path d="M14 4v16" strokeDasharray="2 2" />
  </Icono>
);
export const IconoPerfil = (p: Props) => (
  <Icono {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
  </Icono>
);
export const IconoBuscar = (p: Props) => (
  <Icono {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-4-4" />
  </Icono>
);
export const IconoAtras = (p: Props) => (
  <Icono {...p}>
    <path d="M15 18l-6-6 6-6" />
  </Icono>
);
export const IconoCheck = (p: Props) => (
  <Icono strokeWidth={2.6} {...p}>
    <path d="M5 12l5 5 9-10" />
  </Icono>
);
export const IconoReloj = (p: Props) => (
  <Icono {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Icono>
);
export const IconoEstrella = (p: Props) => (
  <Icono {...p}>
    <path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z" />
  </Icono>
);
export const IconoCandado = (p: Props) => (
  <Icono {...p}>
    <rect x="4" y="10" width="16" height="10" rx="2" />
    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
  </Icono>
);
export const IconoTienda = (p: Props) => (
  <Icono {...p}>
    <path d="M3 10l1-5h16l1 5M4 10v10h16V10M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" />
  </Icono>
);
export const IconoCubiertos = (p: Props) => (
  <Icono {...p}>
    <path d="M7 3v8a3 3 0 0 0 3 3v7M10 3v6M13 3v8M17 3c-2 2-2 6 0 8v10" />
  </Icono>
);
