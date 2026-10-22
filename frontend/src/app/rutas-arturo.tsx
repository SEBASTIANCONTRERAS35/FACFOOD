// Vistas 05–08 · Arturo
import {Route} from "react-router-dom";
import {VistaPendiente} from "../components";
import {RequiereSesion} from "../features/cuenta/sesion";
import {SeguimientoPage} from "../features/seguimiento/SeguimientoPage";
import {VendedorPage} from "../features/vendedor/VendedorPage";
export const rutasArturo=(<><Route path="/pedido/:id" element={<RequiereSesion><SeguimientoPage/></RequiereSesion>}/><Route path="/vendedor" element={<RequiereSesion><VendedorPage/></RequiereSesion>}/><Route path="/repartidor" element={<VistaPendiente numero="07" nombre="Entregas disponibles" responsable="Arturo"/>}/><Route path="/repartidor/entrega/:id" element={<VistaPendiente numero="08" nombre="Entrega en curso" responsable="Arturo"/>}/></>);
