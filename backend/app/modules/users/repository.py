import uuid
from typing import List, Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.users.models import Permission, Role, Sucursal, User


class SucursalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, sucursal_id: uuid.UUID) -> Optional[Sucursal]:
        stmt = select(Sucursal).where(Sucursal.id == sucursal_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Optional[Sucursal]:
        stmt = select(Sucursal).where(Sucursal.codigo == codigo)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, only_active: bool = False) -> Sequence[Sucursal]:
        stmt = select(Sucursal)
        if only_active:
            stmt = stmt.where(Sucursal.activa.is_(True))
        stmt = stmt.order_by(Sucursal.nombre.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, sucursal: Sucursal) -> Sucursal:
        self.db.add(sucursal)
        await self.db.flush()
        await self.db.refresh(sucursal)
        return sucursal


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, permission_id: uuid.UUID) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_ids(self, ids: List[uuid.UUID]) -> Sequence[Permission]:
        stmt = select(Permission).where(Permission.id.in_(ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_all(self) -> Sequence[Permission]:
        stmt = select(Permission).order_by(Permission.module.asc(), Permission.code.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, permission: Permission) -> Permission:
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        return permission


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.code == code)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.name.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, role: Role) -> Role:
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update(self, role: Role) -> Role:
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)
        await self.db.flush()


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.role).selectinload(Role.permissions),
                selectinload(User.sucursal),
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.role).selectinload(Role.permissions),
                selectinload(User.sucursal),
            )
            .where(User.username == username)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.role).selectinload(Role.permissions),
                selectinload(User.sucursal),
            )
            .where(User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Busqueda indistinta por username o email para el flujo de autenticacion."""
        stmt = (
            select(User)
            .options(
                selectinload(User.role).selectinload(Role.permissions),
                selectinload(User.sucursal),
            )
            .where(or_(User.username == identifier, User.email == identifier))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        sucursal_id: Optional[uuid.UUID] = None,
        role_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.role).selectinload(Role.permissions),
                selectinload(User.sucursal),
            )
        )
        if sucursal_id:
            stmt = stmt.where(User.sucursal_id == sucursal_id)
        if role_id:
            stmt = stmt.where(User.role_id == role_id)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        stmt = stmt.order_by(User.last_name.asc(), User.first_name.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: dict) -> User:
        for k, v in data.items():
            if hasattr(user, k):
                setattr(user, k, v)
        await self.db.flush()
        await self.db.refresh(user)
        return user

