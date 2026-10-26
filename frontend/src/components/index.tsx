// Componentes compartidos — equivalen a los componentes del Figma (sección "Componentes").
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";
import { NavLink } from "react-router-dom";
import { useEnLinea } from "../api/conexion";
import { IconoCheck, IconoCubiertos, IconoCupon, IconoPedidos, IconoPerfil, IconoUbicacion } from "./iconos";

// ---- Button (Primary / Secondary) ----
type BotonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variante?: "primario" | "secundario";
  cargando?: boolean;
};

export function Boton({ variante = "primario", cargando = false, disabled, children, className = "", ...resto }: BotonProps) {
  return (
    <button
      className={`boton boton--${variante} ${className}`}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      {...resto}
    >
      {cargando ? "Un momento…" : children}
    </button>
  );
}

// ---- Input ----
type CampoProps = InputHTMLAttributes<HTMLInputElement> & { error?: string; icono?: ReactNode };

export const Campo = forwardRef<HTMLInputElement, CampoProps>(function Campo(
  { error, icono, placeholder, className = "", id, ...resto },
  ref,
) {
  const errorId = error && id ? `${id}-error` : undefined;
  return (
    <div className={className}>
      <label className={`campo ${error ? "campo--error" : ""}`}>
        {icono}
        <span className="solo-lectores">{placeholder}</span>
        <input
          ref={ref}
          id={id}
          placeholder={placeholder}
          aria-invalid={error ? true : undefined}
          aria-describedby={errorId}
          {...resto}
        />
      </label>
      {error && (
        <p className="error-campo" id={errorId}>
          {error}
        </p>
      )}
    </div>
  );
});

// ---- Chip ----
export function Chip({ children, activo = false, onClick }: { children: ReactNode; activo?: boolean; onClick?: () => void }) {
  if (!onClick) return <span className="chip">{children}</span>;
  return (
    <button type="button" className={`chip chip--boton ${activo ? "chip--activo" : ""}`} aria-pressed={activo} onClick={onClick}>
      {children}
    </button>
  );
}

// ---- StallCard (puesto) ----
export function TarjetaPuesto(props: { nombre: string; detalle: string; entrega: string; cerrado?: boolean; onClick?: () => void }) {
  return (
    <button type="button" className={`tarjeta-puesto ${props.cerrado ? "tarjeta-puesto--cerrado" : ""}`} onClick={props.onClick}>
      <span className="tarjeta-puesto__foto" aria-hidden="true">
        <IconoCubiertos tam={28} />
      </span>
      <span className="tarjeta-puesto__info">
        <span className="tarjeta-puesto__nombre">{props.nombre}</span>
        <span className="tarjeta-puesto__detalle">{props.detalle}</span>
        <span className="tarjeta-puesto__entrega">{props.cerrado ? "Cerrado ahora" : props.entrega}</span>
      </span>
    </button>
  );
}

// ---- ProductRow ----
export function FilaProducto(props: {
  nombre: string;
  descripcion: string;
  precio: string;
  cantidad?: number;
  deshabilitado?: boolean;
  onAgregar?: () => void;
  onQuitar?: () => void;
}) {
  return (
    <div className="fila-producto">
      <div className="fila-producto__info">
        <p className="fila-producto__nombre">{props.nombre}</p>
        <p className="fila-producto__desc">{props.descripcion}</p>
        <p className="fila-producto__precio">{props.precio}</p>
      </div>
      {props.onQuitar && !!props.cantidad && (
        <button type="button" className="fila-producto__quitar" onClick={props.onQuitar} aria-label={`Quitar un ${props.nombre}`}>
          −
        </button>
      )}
      <button
        type="button"
        className="fila-producto__agregar"
        onClick={props.onAgregar}
        disabled={props.deshabilitado}
        aria-label={props.cantidad ? `Agregar otro ${props.nombre} (llevas ${props.cantidad})` : `Agregar ${props.nombre}`}
      >
        {props.cantidad ? <span className="fila-producto__cantidad">{props.cantidad}</span> : "+"}
      </button>
    </div>
  );
}

// ---- PasoEstado (Hecho / Actual / Pendiente) ----
export function PasoEstado(props: { estado: "hecho" | "actual" | "pendiente"; titulo: string; detalle?: string }) {
  return (
    <div className={`paso paso--${props.estado}`} aria-current={props.estado === "actual" ? "step" : undefined}>
      <span className="paso__punto" aria-hidden="true">
        {props.estado === "hecho" && <IconoCheck tam={16} />}
        {props.estado === "actual" && <span className="paso__interior" />}
      </span>
      <span>
        <span className="paso__titulo">{props.titulo}</span>
        {props.detalle && <span className="paso__detalle">{props.detalle}</span>}
      </span>
    </div>
  );
}

// ---- BottomNav ----
const NAV = [
  { a: "/explorar", texto: "Explorar", Icono: IconoUbicacion },
  { a: "/pedidos", texto: "Pedidos", Icono: IconoPedidos },
  { a: "/cupones", texto: "Cupones", Icono: IconoCupon },
  { a: "/perfil", texto: "Perfil", Icono: IconoPerfil },
];

export function NavInferior() {
  return (
    <nav className="nav-inferior" aria-label="Principal">
      {NAV.map(({ a, texto, Icono }) => (
        <NavLink key={a} to={a} className={({ isActive }) => `nav-inferior__item ${isActive ? "nav-inferior__item--activo" : ""}`}>
          <Icono />
          <span>{texto}</span>
        </NavLink>
      ))}
    </nav>
  );
}

// ---- Pantalla: contenedor móvil con barra inferior opcional ----
export function Pantalla(props: { children: ReactNode; nav?: boolean; barra?: ReactNode; oscura?: boolean }) {
  return (
    <div className={`pantalla ${props.oscura ? "pantalla--oscura" : ""}`}>
      <main className={`pantalla__contenido ${props.nav || props.barra ? "pantalla__contenido--con-barra" : ""}`}>
        {props.children}
      </main>
      {props.barra && <div className="barra-accion">{props.barra}</div>}
      {props.nav && !props.barra && <NavInferior />}
    </div>
  );
}

// ---- Aviso global cuando no hay conexión (PWA) ----
export function AvisoSinConexion() {
  const enLinea = useEnLinea();
  if (enLinea) return null;
  return (
    <div className="aviso-sin-conexion" role="status">
      Sin conexión · mostrando datos guardados
    </div>
  );
}

// ---- Tarjeta genérica ----
export function Tarjeta({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`tarjeta ${className}`}>{children}</section>;
}

// ---- Vista pendiente (para las vistas que aún no se implementan) ----
export function VistaPendiente({ numero, nombre, responsable }: { numero: string; nombre: string; responsable: string }) {
  return (
    <Pantalla nav>
      <div className="vista-pendiente">
        <p className="marca vista-pendiente__numero">{numero}</p>
        <h1>{nombre}</h1>
        <p className="texto-muted">En construcción · a cargo de {responsable}</p>
      </div>
    </Pantalla>
  );
}
