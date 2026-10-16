import re

from pydantic import BaseModel, field_validator

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CREDENCIAL = re.compile(r"^\d{9}$")


class RegistroEntrada(BaseModel):
    nombre: str
    credencial_unam: str
    correo: str
    password: str
    consentimiento_datos: bool

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
