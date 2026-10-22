// Vistas 05–08 · Arturo
import {Route} from "react-router-dom";
import {RequiereSesion} from "../features/cuenta/sesion";
import {SeguimientoPage} from "../features/seguimiento/SeguimientoPage";
import {VendedorPage} from "../features/vendedor/VendedorPage";
import {RepartidorPage} from "../features/repartidor/RepartidorPage";
import {EntregaPage} from "../features/repartidor/EntregaPage";
export const rutasArturo=(<><Route path="/pedido/:id" element={<RequiereSesion><SeguimientoPage/></RequiereSesion>}/><Route path="/vendedor" element={<RequiereSesion><VendedorPage/></RequiereSesion>}/><Route path="/repartidor" element={<RequiereSesion><RepartidorPage/></RequiereSesion>}/><Route path="/repartidor/entrega/:id" element={<RequiereSesion><EntregaPage/></RequiereSesion>}/></>);
