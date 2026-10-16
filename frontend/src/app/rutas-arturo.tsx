// Vistas 05–08 · Arturo
import { Route } from "react-router-dom";
import { VistaPendiente } from "../components";

export const rutasArturo = (
  <>
    <Route path="/pedido/:id" element={<VistaPendiente numero="05" nombre="Seguimiento del pedido" responsable="Arturo" />} />
    <Route path="/vendedor" element={<VistaPendiente numero="06" nombre="Panel del vendedor" responsable="Arturo" />} />
    <Route path="/repartidor" element={<VistaPendiente numero="07" nombre="Entregas disponibles" responsable="Arturo" />} />
    <Route path="/repartidor/entrega/:id" element={<VistaPendiente numero="08" nombre="Entrega en curso" responsable="Arturo" />} />
  </>
);
