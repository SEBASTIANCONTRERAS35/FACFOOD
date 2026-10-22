import {describe,expect,it} from "vitest";
import {detalleEvento,estadoPaso,horaLocal,tituloEstado} from "./seguimiento";
describe("seguimiento",()=>{
 it("distingue ENVIADA según el método",()=>{expect(detalleEvento("ENVIADA","pickup")).toBe("Listo para recoger en el puesto");expect(detalleEvento("ENVIADA","estudiante")).toBe("El repartidor ya lo recogió y va en camino");});
 it("traduce estados y conserva los desconocidos",()=>{expect(tituloEstado("EN_PREPARACION")).toBe("En preparación");expect(tituloEstado("NUEVO")).toBe("NUEVO");});
 it("clasifica estados previos, actual y terminal",()=>{expect(estadoPaso(false,false,0,3)).toBe("hecho");expect(estadoPaso(true,false,1,3)).toBe("actual");expect(estadoPaso(false,false,2,3)).toBe("pendiente");expect(estadoPaso(false,true,2,3)).toBe("hecho");});
 it("maneja fecha inválida",()=>{expect(horaLocal("no-es-fecha")).toBe("");expect(horaLocal("2026-01-01T13:05:00Z")).not.toBe("");});
});
