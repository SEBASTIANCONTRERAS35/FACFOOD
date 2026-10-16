from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.adapters.postgres.modelos import Base, es_nuestro
from app.shared.config import obtener_config

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=obtener_config().database_url, target_metadata=target_metadata,
                      literal_binds=True, include_object=es_nuestro)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    motor = create_engine(obtener_config().database_url)
    with motor.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata,
                          include_object=es_nuestro)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
