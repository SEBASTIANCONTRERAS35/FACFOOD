def test_de_vendedor_postgres_filtra_y_ordena(fabrica_pg):
    with fabrica_pg() as u:
        puestos=u.puntos_venta.de_vendedor(3)
        assert puestos
        assert [p.id for p in puestos]==sorted(p.id for p in puestos)
        assert all(p.vendedor_id==3 for p in puestos)
