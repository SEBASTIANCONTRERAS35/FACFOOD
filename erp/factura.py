"""
Capa de Dominio - FACFOOD
Módulo ERP: Factura

La factura es el "acta de nacimiento" de la venta: solo existe para una
orden pagada y es inmutable (dataclass frozen).

NOTA: el XML que se genera aquí es una versión SIMPLIFICADA de sandbox, sin
valor fiscal. El timbrado real (CFDI con un PAC y el SAT) es infraestructura
y será un adaptador aparte; el dominio solo conoce el contrato.
"""

import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# RFC de persona moral (12) o física (13)
_PATRON_RFC = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")


class RfcInvalidoError(Exception):
    """Se lanza cuando el RFC del receptor no tiene un formato válido."""


def validar_rfc(rfc: str) -> str:
    rfc = rfc.strip().upper()
    if not _PATRON_RFC.match(rfc):
        raise RfcInvalidoError(f"RFC con formato inválido: {rfc!r}")
    return rfc


@dataclass(frozen=True)
class Factura:
    folio_fiscal: uuid.UUID
    rfc_receptor: str
    xml_data: bytes


def emitir_factura(rfc_receptor, fecha, lineas, subtotal, descuentos, iva, envio, total) -> Factura:
    rfc = validar_rfc(rfc_receptor)
    folio = uuid.uuid4()

    raiz = ET.Element("Comprobante", {
        "Version": "SANDBOX-SIMPLIFICADO",
        "Folio": str(folio),
        "Fecha": fecha.isoformat(),
        "Subtotal": f"{subtotal:.2f}",
        "Descuento": f"{descuentos:.2f}",
        "IVA": f"{iva:.2f}",
        "Envio": f"{envio:.2f}",
        "Total": f"{total:.2f}",
    })
    ET.SubElement(raiz, "Receptor", {"Rfc": rfc})
    conceptos = ET.SubElement(raiz, "Conceptos")
    for linea in lineas:
        ET.SubElement(conceptos, "Concepto", {
            "ProductoID": linea.producto_id,
            "Cantidad": str(linea.cantidad),
            "PrecioUnitario": f"{linea.precio_unitario:.2f}",
            "Importe": f"{linea.subtotal:.2f}",
        })

    xml = ET.tostring(raiz, encoding="utf-8", xml_declaration=True)
    return Factura(folio_fiscal=folio, rfc_receptor=rfc, xml_data=xml)
