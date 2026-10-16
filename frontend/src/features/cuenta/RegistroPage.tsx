// Vista 01 · Registro (LFPDPPP). Ver docs/diseno/01-registro.png
import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../../api/client";
import { Boton, Campo, Pantalla } from "../../components";
import { IconoCheck } from "../../components/iconos";
import { Marca } from "./Marca";
import type { DatosRegistro } from "./sesion";
import { useSesion } from "./sesion";
import "./cuenta.css";

const VACIO: DatosRegistro = { nombre: "", credencial_unam: "", correo: "", password: "", consentimiento_datos: false };

export function RegistroPage() {
  const { registrarse } = useSesion();
  const navegar = useNavigate();
  const desde = (useLocation().state as { desde?: string } | null)?.desde ?? "/explorar";
  const [datos, setDatos] = useState(VACIO);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState("");
  const [enviando, setEnviando] = useState(false);

  const cambiar = (campo: keyof DatosRegistro) => (e: ChangeEvent<HTMLInputElement>) => {
    const valor = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setDatos((d) => ({ ...d, [campo]: valor }));
    setErrores((er) => ({ ...er, [campo]: "" }));
  };

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setGeneral("");
    try {
      await registrarse(datos);
      navegar(desde, { replace: true });
    } catch (err) {
      const error = err as ApiError;
      setErrores(error.campos ?? {});
      if (error.codigo === "CORREO_REGISTRADO") setErrores({ correo: error.message });
      else if (error.codigo === "CREDENCIAL_REGISTRADA") setErrores({ credencial_unam: error.message });
      else if (!Object.keys(error.campos ?? {}).length) setGeneral(error.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Pantalla>
      <form className="cuenta" onSubmit={enviar} noValidate>
        <Marca />
        <h1 className="cuenta__titulo">Crea tu cuenta</h1>

        <div className="cuenta__campos">
          <Campo id="nombre" placeholder="Nombre completo" autoComplete="name" value={datos.nombre}
            onChange={cambiar("nombre")} error={errores.nombre} required />
          <Campo id="credencial_unam" placeholder="Número de cuenta UNAM" inputMode="numeric" maxLength={9}
            value={datos.credencial_unam} onChange={cambiar("credencial_unam")} error={errores.credencial_unam} required />
          <Campo id="correo" type="email" placeholder="Correo institucional" autoComplete="email" value={datos.correo}
            onChange={cambiar("correo")} error={errores.correo} required />
          <Campo id="password" type="password" placeholder="Contraseña (mín. 8 caracteres)" autoComplete="new-password"
            value={datos.password} onChange={cambiar("password")} error={errores.password} required />
        </div>

        <label className="consentimiento">
          <input type="checkbox" checked={datos.consentimiento_datos} onChange={cambiar("consentimiento_datos")} />
          <span className="consentimiento__caja" aria-hidden="true">
            {datos.consentimiento_datos && <IconoCheck tam={16} />}
          </span>
          <span className="consentimiento__texto">
            Acepto el Aviso de Privacidad y el tratamiento de mis datos personales conforme a la LFPDPPP.
            Mi contraseña se guarda cifrada.
          </span>
        </label>

        {general && <p className="error-campo" role="alert">{general}</p>}

        <div className="cuenta__acciones">
          <Boton type="submit" cargando={enviando} disabled={!datos.consentimiento_datos}>
            Crear cuenta
          </Boton>
          <Link to="/login" state={{ desde }} className="boton boton--secundario cuenta__enlace-boton">
            Ya tengo cuenta · Iniciar sesión
          </Link>
        </div>

        <p className="cuenta__nota">Después de 3 pedidos podrás abrir tu propio puesto y vender.</p>
      </form>
    </Pantalla>
  );
}
