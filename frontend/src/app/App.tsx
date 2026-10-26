// Rutas de la app. Cada quien edita SOLO su archivo de rutas para no chocar:
//   rutas-sebastian.tsx  → vistas 01–04
//   rutas-arturo.tsx     → vistas 05–08
import { Route, Routes } from "react-router-dom";
import { AvisoSinConexion, VistaPendiente } from "../components";
import { SelectorUsuarioPrueba } from "../dev/SelectorUsuarioPrueba";
import { Actualizacion } from "../pwa/Actualizacion";
import { Proveedores } from "./proveedores";
import { rutasArturo } from "./rutas-arturo";
import { rutasSebastian } from "./rutas-sebastian";

export default function App() {
  return (
    <Proveedores>
      <AvisoSinConexion />
      <Routes>
        {rutasSebastian}
        {rutasArturo}
        <Route path="/pedidos" element={<VistaPendiente numero="—" nombre="Mis pedidos" responsable="el equipo" />} />
        <Route path="/cupones" element={<VistaPendiente numero="—" nombre="Cupones" responsable="el equipo" />} />
        <Route path="*" element={<VistaPendiente numero="404" nombre="Esta página no existe" responsable="nadie 🙂" />} />
      </Routes>
      <Actualizacion />
      {import.meta.env.DEV && <SelectorUsuarioPrueba />}
    </Proveedores>
  );
}
