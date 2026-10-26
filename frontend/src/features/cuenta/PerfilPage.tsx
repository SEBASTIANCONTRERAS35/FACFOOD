// Perfil: nivel de lealtad, perfil dual y cierre de sesión.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { Boton, Chip, Pantalla, Tarjeta } from "../../components";
import { InstalarApp } from "../../pwa/InstalarApp";
import { useSesion } from "./sesion";
import "./cuenta.css";

const NIVEL = { bronce: "Bronce · sin descuento", plata: "Plata · 5% de descuento", oro: "Oro · 10% de descuento" };

export function PerfilPage() {
  const { usuario, cerrarSesion, recargar } = useSesion();
  const navegar = useNavigate();
  const [error, setError] = useState("");
  if (!usuario) return null;

  async function volverseVendedor() {
    try {
      await api("/usuarios/me/vendedor", { method: "POST" });
      await recargar();
    } catch (e) {
      setError((e as ApiError).message);
    }
  }

  return (
    <Pantalla nav>
      <div className="cuenta">
        <h1 className="cuenta__titulo">{usuario.nombre}</h1>
        <p className="texto-muted">{usuario.correo}</p>
        <Tarjeta>
          <Chip>{NIVEL[usuario.nivel_lealtad]}</Chip>
          <p>
            {usuario.pedidos_completados} pedido{usuario.pedidos_completados === 1 ? "" : "s"} completado
            {usuario.pedidos_completados === 1 ? "" : "s"} · rol: {usuario.rol}
          </p>
        </Tarjeta>
        {usuario.puede_vender && (
          <Tarjeta className="perfil__dual">
            <p><strong>¡Ya llevas 3 pedidos!</strong> Ahora puedes abrir tu propio puesto y vender en FACFOOD.</p>
            <Boton onClick={volverseVendedor}>Quiero vender</Boton>
          </Tarjeta>
        )}
        {error && <p className="error-campo" role="alert">{error}</p>}
        <InstalarApp />
        <Boton variante="secundario" onClick={() => { cerrarSesion(); navegar("/login"); }}>
          Cerrar sesión
        </Boton>
      </div>
    </Pantalla>
  );
}
