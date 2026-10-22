from tests.conftest import como

def test_vendedor_lista_sus_ordenes(cliente):
 r=cliente.get("/vendedor/ordenes",headers=como(3))
 assert r.status_code==200
 assert all(o["punto_venta_id"]==1 for o in r.json()["ordenes"])
 assert all("codigo_entrega" not in o for o in r.json()["ordenes"])
 assert r.json()["puntos_venta"]

def test_no_vendedor_no_lista(cliente):
 assert cliente.get("/vendedor/ordenes",headers=como(1)).status_code==403

def test_transicion_autorizada_registra_evento(cliente,fabrica):
 r=cliente.post("/ordenes/1/estado",headers=como(3),json={"estado":"EN_PREPARACION"})
 assert r.status_code==200 and r.json()["estado"]=="EN_PREPARACION"
 with fabrica() as u:
  ev=u.eventos.de_orden(1)[-1]
  assert ev.estado=="EN_PREPARACION" and ev.actor_id==3 and ev.creado_en

def test_vendedor_no_marca_envio_estudiantil(cliente):
 assert cliente.post("/ordenes/1/estado",headers=como(3),json={"estado":"EN_PREPARACION"}).status_code==200
 assert cliente.post("/ordenes/1/estado",headers=como(3),json={"estado":"ENVIADA"}).status_code==409

def test_orden_ajena_es_inexistente(cliente):
 r=cliente.post("/ordenes/3/estado",headers=como(3),json={"estado":"EN_PREPARACION"})
 assert r.status_code==404

def test_puesto_propio_y_ajeno(cliente):
 assert cliente.patch("/puntos-venta/1",headers=como(3),json={"abierto":False}).status_code==200
 assert cliente.patch("/puntos-venta/2",headers=como(3),json={"abierto":False}).status_code==404
