def test_de_vendedor_memoria_filtra_y_ordena(fabrica):
    with fabrica() as u:
        puestos=u.puntos_venta.de_vendedor(3)
        assert puestos
        assert [p.id for p in puestos]==sorted(p.id for p in puestos)
        assert all(p.vendedor_id==3 for p in puestos)
