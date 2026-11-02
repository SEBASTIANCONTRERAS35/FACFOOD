from app.shared.config import normalizar_url_bd


def test_url_de_neon_o_render_usa_psycopg():
    neon = "postgresql://usuario:clave@ep-algo.us-east-2.aws.neon.tech/facfood?sslmode=require"
    assert normalizar_url_bd(neon) == (
        "postgresql+psycopg://usuario:clave@ep-algo.us-east-2.aws.neon.tech/facfood?sslmode=require"
    )
    assert normalizar_url_bd("postgres://u:c@host:5432/db") == "postgresql+psycopg://u:c@host:5432/db"


def test_url_que_ya_trae_el_controlador_no_cambia():
    url = "postgresql+psycopg://facfood:facfood@localhost:5432/facfood"
    assert normalizar_url_bd(url) == url
