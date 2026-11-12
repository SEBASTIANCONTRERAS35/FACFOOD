// Regreso desde Stripe Checkout: /pedido/:id/pago?resultado=exito|cancelado
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { Pantalla } from "../../components";
import { useCarrito } from "./carrito";
import { esperarPago } from "./pago";
import type { Orden } from "./tipos";
import "./carrito.css";

type Estado = "confirmando" | "pendiente" | "cancelando" | "error";

export function PagoResultadoPage() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const { despachar } = useCarrito();
  const navegar = useNavigate();
  const cancelado = params.get("resultado") === "cancelado";
  const [estado, setEstado] = useState<Estado>(cancelado ? "cancelando" : "confirmando");
  const [mensaje, setMensaje] = useState("");
  const iniciado = useRef(false);

  useEffect(() => {
    if (iniciado.current || !id) return;
    iniciado.current = true;
    const confirmar = () =>
      esperarPago(() => api<Orden>(`/ordenes/${id}`)).then((r) => {
        if (r === "pagada") {
          despachar({ tipo: "vaciar" });
          navegar(`/pedido/${id}`, { replace: true });
        } else setEstado("pendiente");
      });

    if (!cancelado) {
      confirmar();
      return;
    }
    // Canceló en Stripe: se cierra el cobro para poder editar el pedido y se regresa al carrito.
    api<Orden>(`/ordenes/${id}/checkout`, { method: "DELETE" })
      .then(() => navegar("/carrito", { replace: true }))
      .catch((e: ApiError) => {
        if (e.codigo === "PAGO_YA_REALIZADO") {
          setEstado("confirmando");
          confirmar();
        } else {
          setMensaje(e.message);
          setEstado("error");
        }
      });
  }, [id, cancelado, despachar, navegar]);

  return (
    <Pantalla nav>
      <div className="seccion carrito__vacio" role="status" aria-live="polite">
        {estado === "confirmando" && (
          <>
            <h1>Confirmando tu pago…</h1>
            <p className="texto-muted">Estamos esperando la confirmación del banco. No cierres esta pantalla.</p>
          </>
        )}
        {estado === "cancelando" && <h1>Regresando a tu pedido…</h1>}
        {estado === "pendiente" && (
          <>
            <h1>Tu pago se está procesando</h1>
            <p className="texto-muted">Aún no recibimos la confirmación. En cuanto llegue, lo verás en Mis pedidos.</p>
            <Link to="/pedidos" className="boton boton--primario carrito__enlace">Ir a Mis pedidos</Link>
          </>
        )}
        {estado === "error" && (
          <>
            <h1>No pudimos regresar a tu pedido</h1>
            <p className="error-campo" role="alert">{mensaje}</p>
            <Link to="/carrito" className="boton boton--primario carrito__enlace">Volver al carrito</Link>
          </>
        )}
      </div>
    </Pantalla>
  );
}
