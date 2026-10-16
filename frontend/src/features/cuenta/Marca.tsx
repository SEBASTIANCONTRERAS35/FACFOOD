import { IconoCubiertos } from "../../components/iconos";

export function Marca() {
  return (
    <div className="marca-facfood">
      <div className="marca-facfood__fila">
        <span className="marca-facfood__logo" aria-hidden="true">
          <IconoCubiertos tam={26} />
        </span>
        <span className="marca marca-facfood__nombre">FACFOOD</span>
      </div>
      <p className="texto-muted">La comida de CU, a un clic.</p>
    </div>
  );
}
