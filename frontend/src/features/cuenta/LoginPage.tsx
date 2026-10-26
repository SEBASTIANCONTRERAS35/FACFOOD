// Vista 01 · Iniciar sesión
import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../../api/client";
import { useEnLinea } from "../../api/conexion";
import { Boton, Campo, Pantalla } from "../../components";
import { Marca } from "./Marca";
import { useSesion } from "./sesion";
import "./cuenta.css";

export function LoginPage() {
  const { iniciarSesion } = useSesion();
  const navegar = useNavigate();
  const desde = (useLocation().state as { desde?: string } | null)?.desde ?? "/explorar";
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const enLinea = useEnLinea();

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await iniciarSesion(correo, password);
      navegar(desde, { replace: true });
    } catch (err) {
      setError((err as ApiError).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Pantalla>
      <form className="cuenta" onSubmit={enviar}>
        <Marca />
        <h1 className="cuenta__titulo">Inicia sesión</h1>
        <div className="cuenta__campos">
          <Campo id="correo" type="email" placeholder="Correo institucional" autoComplete="email"
            value={correo} onChange={(e) => setCorreo(e.target.value)} required />
          <Campo id="password" type="password" placeholder="Contraseña" autoComplete="current-password"
            value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="error-campo" role="alert">{error}</p>}
        <div className="cuenta__acciones">
          <Boton type="submit" cargando={enviando} disabled={!correo || !password || !enLinea}>Iniciar sesión</Boton>
          <Link to="/registro" state={{ desde }} className="boton boton--secundario cuenta__enlace-boton">
            Crear una cuenta nueva
          </Link>
        </div>
      </form>
    </Pantalla>
  );
}
