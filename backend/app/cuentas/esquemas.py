import re

from pydantic import BaseModel, Field, field_validator

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CREDENCIAL = re.compile(r"^\d{9}$")


class RegistroEntrada(BaseModel):
    nombre: str = Field(description="De 2 a 120 caracteres", examples=["Ana López"])
    credencial_unam: str = Field(description="Número de cuenta UNAM: 9 dígitos", examples=["320123456"])
    correo: str = Field(description="Correo válido; se guarda en minúsculas", examples=["ana@comunidad.unam.mx"])
    password: str = Field(description="De 8 a 72 caracteres; solo se guarda su hash (bcrypt)", examples=["segura123"])
    consentimiento_datos: bool = Field(description="Debe ser `true` (Art. 7 LFPDPPP)", examples=[True])

    @field_validator("nombre")
    @classmethod
    def _nombre(cls, v: str) -> str:
        v = " ".join(v.split())
        if not 2 <= len(v) <= 120:
            raise ValueError("Escribe tu nombre completo")
        return v

    @field_validator("credencial_unam")
    @classmethod
    def _credencial(cls, v: str) -> str:
        v = v.strip()
        if not _CREDENCIAL.match(v):
            raise ValueError("El número de cuenta UNAM tiene 9 dígitos")
        return v

    @field_validator("correo")
    @classmethod
    def _correo(cls, v: str) -> str:
        v = v.strip().lower()
        if not _CORREO.match(v) or len(v) > 254:
            raise ValueError("Escribe un correo válido")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if len(v.encode("utf-8")) > 72:  # límite de bcrypt
            raise ValueError("La contraseña es demasiado larga (máximo 72 caracteres)")
        return v


class LoginEntrada(BaseModel):
    correo: str
    password: str

    @field_validator("correo")
    @classmethod
    def _correo(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioSalida(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: str
    pedidos_completados: int
    nivel_lealtad: str
    puede_vender: bool


class SesionSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida
