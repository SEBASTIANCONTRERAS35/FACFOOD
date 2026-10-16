// Vistas 01–04 · Sebastián
import { Navigate, Route } from "react-router-dom";
import { VistaPendiente } from "../components";
import { LoginPage } from "../features/cuenta/LoginPage";
import { PerfilPage } from "../features/cuenta/PerfilPage";
import { RegistroPage } from "../features/cuenta/RegistroPage";
import { RequiereSesion } from "../features/cuenta/sesion";
import { ExplorarPage } from "../features/explorar/ExplorarPage";

export const rutasSebastian = (
  <>
    <Route path="/" element={<Navigate to="/explorar" replace />} />
    <Route path="/registro" element={<RegistroPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/perfil" element={<RequiereSesion><PerfilPage /></RequiereSesion>} />
    <Route path="/explorar" element={<ExplorarPage />} />
    <Route path="/puesto/:id" element={<VistaPendiente numero="03" nombre="Menú del puesto" responsable="Sebastián" />} />
    <Route path="/carrito" element={<VistaPendiente numero="04" nombre="Carrito y pago" responsable="Sebastián" />} />
  </>
);
