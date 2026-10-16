# Diseño UML de la capa de dominio — Módulo ERP (FACFOOD)

## Clases

```mermaid
classDiagram
    class Orden {
        +EstadoOrden estado
        +date fecha
        +Decimal subtotal
        +Decimal descuentos
        +Decimal iva
        +Decimal envio
        +Decimal total
        +str origen_descuento
        +agregar_linea(producto_id, cantidad)
        +aplicar_cupon(cupon)
        +quitar_cupon()
        +definir_lealtad(pedidos_completados)
        +definir_entrega(metodo, distancia_km)
        +definir_envio(monto)
        +avanzar_estado(nuevo)
        +generar_factura(rfc_receptor)
        +dividir_pago(comision_pct, retencion_pct)
    }
    class LineaPedido {
        +str producto_id
        +int cantidad
        +Decimal precio_unitario
        +Decimal subtotal
    }
    class Factura {
        +UUID folio_fiscal
        +str rfc_receptor
        +bytes xml_data
    }
    class DivisionPago {
        +Decimal base
        +Decimal comision_plataforma
        +Decimal retencion
        +Decimal neto_vendedor
    }
    class Cupon {
        +str codigo
        +float porcentaje
        +calcular_descuento(subtotal, hoy)
        +registrar_uso()
    }
    Orden "1" *-- "1..*" LineaPedido
    Orden "1" -- "0..1" Factura : solo en estado PAGADA
    Orden ..> DivisionPago : crea
    Orden ..> Cupon : usa (CRM)
    Orden ..> MetodoDeEntrega : calcula el envío (Strategy)
```

## Máquina de estados de la orden

```mermaid
stateDiagram-v2
    [*] --> CREADA
    CREADA --> PAGADA
    CREADA --> CANCELADA
    PAGADA --> EN_PREPARACION
    EN_PREPARACION --> ENVIADA
    ENVIADA --> ENTREGADA
    ENTREGADA --> [*]
    CANCELADA --> [*]
```

Regla: la secuencia es estricta e irreversible; está prohibido saltar estados.

## Fórmula del total

`Total = (Subtotal - Descuentos) + IVA(16%) + Envío`

El IVA se calcula sobre el monto ya con descuento.

Descuentos: no se acumulan. Se aplica el mayor entre el cupón y el nivel de
lealtad del comprador; el cupón solo se consume al pagar y solo si fue el que
se aplicó.
