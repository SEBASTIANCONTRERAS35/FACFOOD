// Pago con pasarela (ADR 004). La orden queda PAGADA cuando Stripe avisa al servidor (webhook),
// no cuando el navegador regresa: por eso al volver se consulta la orden hasta verla pagada.
import type { Orden } from "./tipos";

export type SesionPago = {
  pasarela: "simulado" | "stripe";
  orden_id: number;
  url: string | null; // página de pago de Stripe; null con el simulado
  monto: string;
  expira_en: string | null;
};

export type ResultadoEspera = "pagada" | "pendiente";

/** Consulta la orden cada `intervaloMs` hasta que deje de estar CREADA o se acaben los intentos. */
export async function esperarPago(
  consultar: () => Promise<Pick<Orden, "estado">>,
  { intentos = 30, intervaloMs = 2000, dormir = (ms: number) => new Promise<void>((r) => setTimeout(r, ms)) } = {},
): Promise<ResultadoEspera> {
  for (let i = 0; i < intentos; i++) {
    try {
      if ((await consultar()).estado !== "CREADA") return "pagada";
    } catch {
      // Un fallo de red momentáneo no significa que el pago falló: se vuelve a intentar.
    }
    if (i < intentos - 1) await dormir(intervaloMs);
  }
  return "pendiente";
}
