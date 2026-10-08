"""
Capa de Dominio - FACFOOD
Entidad Usuario / Perfil (Sprint 2)

Paso 1 (Entidad de Dominio): clase Usuario pura, sin dependencias de
base de datos ni frameworks.

Paso 2 (Regla Core de Negocio): FACFOOD es un marketplace de comida no
oficial dentro de CU, así que la regla de negocio elegida es el
PERFIL DUAL: un usuario empieza como comprador y puede convertirse en
vendedor (quien ofrece comida) cumpliendo una condición mínima de
confianza (haber completado varios pedidos como comprador primero).

Paso 3 (Cumplimiento LFPDPPP & Seguridad), ley vigente desde el
20/marzo/2025:
- Artículo 18: obliga a implementar medidas de seguridad TÉCNICAS que
  protejan los datos contra acceso no autorizado. Por eso la contraseña
  nunca se guarda en texto plano, solo su hash (bcrypt, con salt
  incorporado automáticamente).
- Artículo 7: todo tratamiento de datos personales requiere el
  consentimiento del titular. Por eso Usuario exige la bandera
  `consentimiento_datos` para poder registrarse.
"""

import bcrypt


class ConsentimientoRequeridoError(Exception):
    """Se lanza si se intenta registrar un usuario sin su consentimiento (Art. 7 LFPDPPP)."""


class PerfilNoElegibleError(Exception):
    """Se lanza si un usuario intenta convertirse en vendedor sin cumplir el requisito mínimo."""


class Usuario:
    PEDIDOS_MINIMOS_PARA_VENDEDOR = 3

    def __init__(self, nombre: str, credencial_unam: str, consentimiento_datos: bool):
        if not consentimiento_datos:
            raise ConsentimientoRequeridoError(
                "No se puede registrar al usuario sin su consentimiento de datos (Art. 7 LFPDPPP)"
            )

        self.nombre = nombre
        self.credencial_unam = credencial_unam
        self.consentimiento_datos = consentimiento_datos
        self._password_hash: bytes | None = None

        # Paso 2: perfil dual — todo usuario inicia como comprador
        self.rol = "comprador"
        self.pedidos_completados = 0

    # ---- Paso 2: Regla Core de Negocio (Perfil Dual) ----
    def registrar_pedido_completado(self) -> None:
        self.pedidos_completados += 1

    def convertirse_en_vendedor(self) -> None:
        """Cambia el perfil de comprador a vendedor (perfil dual de marketplace)."""
        if self.pedidos_completados < self.PEDIDOS_MINIMOS_PARA_VENDEDOR:
            raise PerfilNoElegibleError(
                f"Se requieren al menos {self.PEDIDOS_MINIMOS_PARA_VENDEDOR} pedidos "
                f"completados como comprador antes de poder vender comida"
            )
        self.rol = "vendedor"

    # ---- Paso 3: hashing (Art. 18 LFPDPPP) ----
    def registrar_password(self, password_plano: str) -> None:
        """Genera y guarda el hash (Art. 18 LFPDPPP); nunca se guarda el texto plano."""
        salt = bcrypt.gensalt()
        self._password_hash = bcrypt.hashpw(password_plano.encode("utf-8"), salt)

    def verificar_password(self, password_intento: str) -> bool:
        if self._password_hash is None:
            return False
        return bcrypt.checkpw(password_intento.encode("utf-8"), self._password_hash)

    @property
    def password_hash(self) -> bytes | None:
        """Solo expone el hash (nunca la contraseña original)."""
        return self._password_hash
