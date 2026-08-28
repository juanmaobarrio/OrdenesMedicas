import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    EntityAlreadyExistsException,
    EntityNotFoundException,
    ForbiddenActionException,
    InvalidCredentialsException,
)
from backend.app.core.security import get_password_hash, verify_password
from backend.app.modules.users.models import Permission, Role, Sucursal, User
from backend.app.modules.users.repository import (
    PermissionRepository,
    RoleRepository,
    SucursalRepository,
    UserRepository,
)
from backend.app.modules.users.schemas import (
    RoleCreate,
    RoleUpdate,
    SucursalCreate,
    SucursalUpdate,
    UserCreate,
    UserPasswordUpdate,
    UserUpdate,
)


class SucursalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SucursalRepository(db)

    async def list_sucursales(self, only_active: bool = False) -> Sequence[Sucursal]:
        return await self.repo.list_all(only_active=only_active)

    async def get_by_id(self, sucursal_id: uuid.UUID) -> Sucursal:
        sucursal = await self.repo.get_by_id(sucursal_id)
        if not sucursal:
            raise EntityNotFoundException("Sucursal", sucursal_id)
        return sucursal

    async def create_sucursal(self, dto: SucursalCreate) -> Sucursal:
        existing = await self.repo.get_by_codigo(dto.codigo)
        if existing:
            raise EntityAlreadyExistsException("Sucursal", "codigo", dto.codigo)

        sucursal = Sucursal(
            nombre=dto.nombre,
            codigo=dto.codigo.upper().strip(),
            activa=dto.activa,
        )
        return await self.repo.create(sucursal)


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.perm_repo = PermissionRepository(db)

    async def list_roles(self) -> Sequence[Role]:
        return await self.role_repo.list_all()

    async def get_by_id(self, role_id: uuid.UUID) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise EntityNotFoundException("Rol", role_id)
        return role

    async def create_role(self, dto: RoleCreate) -> Role:
        existing = await self.role_repo.get_by_code(dto.code)
        if existing:
            raise EntityAlreadyExistsException("Rol", "codigo", dto.code)

        role = Role(
            code=dto.code.upper().strip(),
            name=dto.name,
            description=dto.description,
            hierarchy_level=dto.hierarchy_level if dto.hierarchy_level is not None else 10,
            is_system=False,
        )

        if dto.permission_ids:
            permissions = await self.perm_repo.list_by_ids(dto.permission_ids)
            role.permissions = list(permissions)

        return await self.role_repo.create(role)

    async def list_permissions(self) -> Sequence[Permission]:
        return await self.perm_repo.list_all()

    async def update_role(self, role_id: uuid.UUID, dto: RoleUpdate) -> Role:
        role = await self.get_by_id(role_id)
        if dto.name is not None:
            role.name = dto.name.strip()
        if dto.description is not None:
            role.description = dto.description.strip() if dto.description else None
        if dto.hierarchy_level is not None:
            role.hierarchy_level = dto.hierarchy_level
        if dto.permission_ids is not None:
            permissions = await self.perm_repo.list_by_ids(dto.permission_ids)
            role.permissions = list(permissions)

        return await self.role_repo.update(role)

    async def delete_role(self, role_id: uuid.UUID) -> None:
        role = await self.get_by_id(role_id)
        if role.is_system:
            raise ForbiddenActionException("No se pueden eliminar los roles base del sistema")
        await self.role_repo.delete(role)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.sucursal_repo = SucursalRepository(db)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("Usuario", user_id)
        return user

    async def list_users(
        self,
        sucursal_id: Optional[uuid.UUID] = None,
        role_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[User]:
        return await self.user_repo.list_all(
            sucursal_id=sucursal_id, role_id=role_id, is_active=is_active
        )

    async def create_user(self, dto: UserCreate, current_user: Optional[User] = None) -> User:
        # Validar username unico
        if await self.user_repo.get_by_username(dto.username):
            raise EntityAlreadyExistsException("Usuario", "username", dto.username)

        # Validar email unico
        if await self.user_repo.get_by_email(dto.email):
            raise EntityAlreadyExistsException("Usuario", "email", dto.email)

        # Validar que exista el rol
        role = await self.role_repo.get_by_id(dto.role_id)
        if not role:
            raise EntityNotFoundException("Rol", dto.role_id)

        # Validar jerarquia de roles si el creador no es Superadmin / Admin
        if current_user:
            is_admin = current_user.is_superuser or (
                current_user.role and current_user.role.code == "ADMIN"
            )
            if not is_admin:
                current_level = current_user.role.hierarchy_level if current_user.role else 0
                target_level = role.hierarchy_level
                if target_level >= current_level:
                    raise ForbiddenActionException(
                        f"No puedes crear usuarios con rol '{role.name}' (jerarquía {target_level}) porque es igual o superior a tu nivel actual ({current_level})."
                    )

        # Validar sucursal si fue provista
        if dto.sucursal_id:
            sucursal = await self.sucursal_repo.get_by_id(dto.sucursal_id)
            if not sucursal:
                raise EntityNotFoundException("Sucursal", dto.sucursal_id)

        user = User(
            username=dto.username.strip(),
            email=dto.email.strip().lower(),
            hashed_password=get_password_hash(dto.password),
            first_name=dto.first_name.strip(),
            last_name=dto.last_name.strip(),
            is_active=dto.is_active,
            is_superuser=dto.is_superuser,
            role_id=dto.role_id,
            sucursal_id=dto.sucursal_id,
        )

        created_user = await self.user_repo.create(user)
        # Recargar con relaciones
        return await self.get_user_by_id(created_user.id)

    async def update_user(self, user_id: uuid.UUID, dto: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)

        if dto.email and dto.email.lower() != user.email:
            existing_email = await self.user_repo.get_by_email(dto.email.lower())
            if existing_email and existing_email.id != user_id:
                raise EntityAlreadyExistsException("Usuario", "email", dto.email)
            user.email = dto.email.lower()

        if dto.first_name is not None:
            user.first_name = dto.first_name.strip()

        if dto.last_name is not None:
            user.last_name = dto.last_name.strip()

        if dto.is_active is not None:
            user.is_active = dto.is_active

        if dto.role_id is not None:
            role = await self.role_repo.get_by_id(dto.role_id)
            if not role:
                raise EntityNotFoundException("Rol", dto.role_id)
            user.role_id = dto.role_id

        if dto.sucursal_id is not None:
            sucursal = await self.sucursal_repo.get_by_id(dto.sucursal_id)
            if not sucursal:
                raise EntityNotFoundException("Sucursal", dto.sucursal_id)
            user.sucursal_id = dto.sucursal_id

        await self.db.flush()
        return await self.get_user_by_id(user_id)

    async def change_password(self, user_id: uuid.UUID, dto: UserPasswordUpdate) -> bool:
        user = await self.get_user_by_id(user_id)
        if not verify_password(dto.current_password, user.hashed_password):
            raise InvalidCredentialsException("La contrasena actual no es correcta")

        user.hashed_password = get_password_hash(dto.new_password)
        await self.db.flush()
        return True

    async def reset_password_by_admin(self, user_id: uuid.UUID, new_password: str) -> bool:
        user = await self.get_user_by_id(user_id)
        user.hashed_password = get_password_hash(new_password)
        await self.db.flush()
        return True

    async def toggle_active(self, user_id: uuid.UUID) -> User:
        user = await self.get_user_by_id(user_id)
        user.is_active = not user.is_active
        await self.db.flush()
        return user

