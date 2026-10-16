// El dinero llega de la API como texto ("65.08"). Aquí solo se muestra;
// para sumar en el carrito se usan centavos enteros, nunca floats.

export function aCentavos(monto: string): number {
  const [enteros, dec = ""] = monto.trim().split(".");
  const signo = enteros.startsWith("-") ? -1 : 1;
  return signo * (Math.abs(parseInt(enteros, 10)) * 100 + parseInt((dec + "00").slice(0, 2), 10));
}

export function desdeCentavos(centavos: number): string {
  const signo = centavos < 0 ? "-" : "";
  const abs = Math.abs(centavos);
  return `${signo}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}

const formato = new Intl.NumberFormat("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function pesos(monto: string): string {
  const centavos = aCentavos(monto);
  const texto = formato.format(Math.abs(centavos) / 100);
  return `${centavos < 0 ? "−" : ""}$${texto}`;
}
