from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Excepcion base personalizada para la aplicacion."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Ha ocurrido un error en la operacion",
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class EntityNotFoundException(AppException):
    """Excepcion cuando un recurso no es encontrado."""
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} con identificador '{entity_id}' no fue encontrado.",
        )


class EntityAlreadyExistsException(AppException):
    """Excepcion cuando se intenta crear un recurso duplicado."""
    def __init__(self, entity_name: str, field_name: str, value: Any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity_name} con {field_name} '{value}' ya existe en el sistema.",
        )


class InvalidCredentialsException(AppException):
    """Excepcion para credenciales invalidas en autenticacion."""
    def __init__(self, detail: str = "Credenciales de acceso incorrectas"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenActionException(AppException):
    """Excepcion para permisos insuficientes."""
    def __init__(self, detail: str = "No tienes permisos suficientes para realizar esta accion"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
