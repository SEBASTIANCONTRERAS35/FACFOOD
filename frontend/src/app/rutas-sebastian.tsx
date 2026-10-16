// Vistas 01–04 · Sebastián
import { Navigate, Route } from "react-router-dom";
import { VistaPendiente } from "../components";

export const rutasSebastian = (
  <>
    <Route path="/" element={<Navigate to="/explorar" replace />} />
    <Route path="/registro" element={<VistaPendiente numero="01" nombre="Registro" responsable="Sebastián" />} />
    <Route path="/login" element={<VistaPendiente numero="01" nombre="Iniciar sesión" responsable="Sebastián" />} />
    <Route path="/explorar" element={<VistaPendiente numero="02" nombre="Explorar puestos" responsable="Sebastián" />} />
    <Route path="/puesto/:id" element={<VistaPendiente numero="03" nombre="Menú del puesto" responsable="Sebastián" />} />
    <Route path="/carrito" element={<VistaPendiente numero="04" nombre="Carrito y pago" responsable="Sebastián" />} />
    <Route path="/perfil" element={<VistaPendiente numero="—" nombre="Perfil" responsable="Sebastián" />} />
  </>
);
