<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { usersService } from '../../services/users.service';
import { useAuthStore } from '../../stores/auth.store';
import { Permission, Role, RoleCreate, RoleUpdate, Sucursal, UserDetail } from '../../types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import Checkbox from 'primevue/checkbox';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import { useToast } from 'primevue/usetoast';
import { getErrorMessage } from '../../services/api';

const toast = useToast();
const authStore = useAuthStore();

const users = ref<UserDetail[]>([]);
const roles = ref<Role[]>([]);
const permissions = ref<Permission[]>([]);
const sucursales = ref<Sucursal[]>([]);
const isLoading = ref(false);

// Filtros
const searchUser = ref('');
const filterActiveStatus = ref<'all' | 'active' | 'inactive'>('all');

// Modal User (Crear / Editar)
const isUserDialogVisible = ref(false);
const isEditingUser = ref(false);
const editingUserId = ref<string | null>(null);
const isSavingUser = ref(false);

const userForm = ref<{
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role_id: string;
  sucursal_id: string | null;
  is_active: boolean;
}>({
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  role_id: '',
  sucursal_id: null,
  is_active: true,
});

// Modal Reset Password (Admin)
const isResetPasswordDialogVisible = ref(false);
const resetPasswordUserId = ref<string | null>(null);
const resetPasswordUsername = ref<string>('');
const newAdminPassword = ref<string>('');
const isSavingResetPassword = ref(false);

// Modal Role
const isRoleDialogVisible = ref(false);
const isEditingRole = ref(false);
const isSavingRole = ref(false);
const editingRoleId = ref<string | null>(null);

const roleForm = ref<{
  code: string;
  name: string;
  description: string;
  hierarchy_level: number;
  permission_ids: string[];
}>({
  code: '',
  name: '',
  description: '',
  hierarchy_level: 10,
  permission_ids: [],
});

const loadData = async () => {
  isLoading.value = true;
  try {
    const activeParam =
      filterActiveStatus.value === 'all'
        ? undefined
        : filterActiveStatus.value === 'active';

    const [usersRes, rolesRes, permsRes, sucRes] = await Promise.all([
      usersService.listUsers(undefined, undefined, activeParam),
      usersService.listRoles(),
      authStore.isAdmin ? usersService.listPermissions() : Promise.resolve([]),
      usersService.listSucursales(),
    ]);
    users.value = usersRes;
    roles.value = rolesRes;
    permissions.value = permsRes;
    sucursales.value = sucRes;
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los datos de usuarios', life: 3000 });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadData();
});

// Jerarquía de Roles disponibles para crear usuarios
const availableRolesForCreation = computed(() => {
  if (authStore.isAdmin || authStore.user?.is_superuser) {
    return roles.value;
  }
  const myCode = authStore.user?.role_code;
  const myLevel =
    authStore.user?.hierarchy_level ||
    (myCode === 'ADMIN' ? 100 : myCode === 'AUDITOR' ? 50 : 10);
  return roles.value.filter((r) => (r.hierarchy_level || 10) < myLevel);
});

// Usuarios filtrados por búsqueda
const filteredUsers = computed(() => {
  let list = users.value;
  const q = searchUser.value.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (u) =>
        u.username.toLowerCase().includes(q) ||
        u.full_name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.role?.name && u.role.name.toLowerCase().includes(q))
    );
  }
  return list;
});

// Permisos agrupados por módulo
const permissionsByModule = computed(() => {
  const grouped: Record<string, Permission[]> = {};
  permissions.value.forEach((p) => {
    if (!grouped[p.module]) grouped[p.module] = [];
    grouped[p.module].push(p);
  });
  return grouped;
});

// Acciones Usuario
const handleOpenCreateUser = () => {
  isEditingUser.value = false;
  editingUserId.value = null;
  userForm.value = {
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role_id: availableRolesForCreation.value[0]?.id || '',
    sucursal_id: null,
    is_active: true,
  };
  isUserDialogVisible.value = true;
};

const handleOpenEditUser = (u: UserDetail) => {
  isEditingUser.value = true;
  editingUserId.value = u.id;
  userForm.value = {
    username: u.username,
    email: u.email,
    password: '',
    first_name: u.first_name,
    last_name: u.last_name,
    role_id: u.role?.id || '',
    sucursal_id: u.sucursal?.id || null,
    is_active: u.is_active,
  };
  isUserDialogVisible.value = true;
};

const handleSaveUser = async () => {
  if (
    !userForm.value.username?.trim() ||
    !userForm.value.email?.trim() ||
    (!isEditingUser.value && !userForm.value.password) ||
    !userForm.value.first_name?.trim() ||
    !userForm.value.last_name?.trim() ||
    !userForm.value.role_id
  ) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Complete todos los campos obligatorios', life: 3000 });
    return;
  }

  if (!isEditingUser.value && userForm.value.password.length < 6) {
    toast.add({
      severity: 'warn',
      summary: 'Contraseña muy corta',
      detail: 'La contraseña debe tener al menos 6 caracteres',
      life: 3500,
    });
    return;
  }

  isSavingUser.value = true;
  try {
    if (isEditingUser.value && editingUserId.value) {
      await usersService.updateUser(editingUserId.value, {
        email: userForm.value.email.trim().toLowerCase(),
        first_name: userForm.value.first_name.trim(),
        last_name: userForm.value.last_name.trim(),
        role_id: userForm.value.role_id,
        sucursal_id: userForm.value.sucursal_id ? userForm.value.sucursal_id : null,
        is_active: userForm.value.is_active,
      } as any);
      toast.add({ severity: 'success', summary: 'Usuario Actualizado', detail: 'Datos guardados correctamente', life: 3000 });
    } else {
      await usersService.createUser({
        username: userForm.value.username.trim(),
        email: userForm.value.email.trim().toLowerCase(),
        password: userForm.value.password,
        first_name: userForm.value.first_name.trim(),
        last_name: userForm.value.last_name.trim(),
        role_id: userForm.value.role_id,
        sucursal_id: userForm.value.sucursal_id,
        is_active: userForm.value.is_active,
      });
      toast.add({ severity: 'success', summary: 'Usuario Creado', detail: 'Nuevo usuario registrado con éxito', life: 3000 });
    }
    isUserDialogVisible.value = false;
    await loadData();
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error al Guardar Usuario',
      detail: getErrorMessage(err, 'No se pudo registrar o actualizar el usuario'),
      life: 4500,
    });
  } finally {
    isSavingUser.value = false;
  }
};

const handleToggleActiveUser = async (u: UserDetail) => {
  try {
    await usersService.toggleActiveUser(u.id);
    toast.add({
      severity: 'info',
      summary: u.is_active ? 'Usuario Inactivado' : 'Usuario Activado',
      detail: `La cuenta de ${u.username} ahora está ${u.is_active ? 'inactiva' : 'activa'}.`,
      life: 3000,
    });
    await loadData();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al cambiar estado', life: 3000 });
  }
};

// Reset Password por Admin
const handleOpenResetPassword = (u: UserDetail) => {
  resetPasswordUserId.value = u.id;
  resetPasswordUsername.value = u.username;
  newAdminPassword.value = '';
  isResetPasswordDialogVisible.value = true;
};

const handleSaveResetPassword = async () => {
  if (!newAdminPassword.value || newAdminPassword.value.length < 6) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'La nueva contraseña debe tener al menos 6 caracteres', life: 3000 });
    return;
  }

  isSavingResetPassword.value = true;
  try {
    await usersService.resetPasswordByAdmin(resetPasswordUserId.value!, newAdminPassword.value);
    toast.add({
      severity: 'success',
      summary: 'Contraseña Restablecida',
      detail: `Se actualizó la contraseña para el usuario ${resetPasswordUsername.value}`,
      life: 4000,
    });
    isResetPasswordDialogVisible.value = false;
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: getErrorMessage(err, 'No se pudo restablecer la contraseña'),
      life: 4000,
    });
  } finally {
    isSavingResetPassword.value = false;
  }
};

// Acciones Roles
const handleOpenCreateRole = () => {
  isEditingRole.value = false;
  editingRoleId.value = null;
  roleForm.value = {
    code: '',
    name: '',
    description: '',
    hierarchy_level: 10,
    permission_ids: [],
  };
  isRoleDialogVisible.value = true;
};

const handleOpenEditRole = (r: Role) => {
  isEditingRole.value = true;
  editingRoleId.value = r.id;
  roleForm.value = {
    code: r.code,
    name: r.name,
    description: r.description || '',
    hierarchy_level: (r as any).hierarchy_level || 10,
    permission_ids: r.permissions.map((p) => p.id),
  };
  isRoleDialogVisible.value = true;
};

const handleSaveRole = async () => {
  if (!roleForm.value.name.trim() || (!isEditingRole.value && !roleForm.value.code.trim())) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Código y Nombre del rol son obligatorios', life: 3000 });
    return;
  }

  isSavingRole.value = true;
  try {
    if (isEditingRole.value && editingRoleId.value) {
      const payload: RoleUpdate = {
        name: roleForm.value.name.trim(),
        description: roleForm.value.description.trim() || null as any,
        hierarchy_level: roleForm.value.hierarchy_level,
        permission_ids: roleForm.value.permission_ids,
      };
      await usersService.updateRole(editingRoleId.value, payload);
      toast.add({ severity: 'success', summary: 'Rol Actualizado', detail: 'Permisos y rol modificados con éxito', life: 3000 });
    } else {
      const payload: RoleCreate = {
        code: roleForm.value.code.trim().toUpperCase(),
        name: roleForm.value.name.trim(),
        description: roleForm.value.description.trim() || null as any,
        hierarchy_level: roleForm.value.hierarchy_level,
        permission_ids: roleForm.value.permission_ids,
      };
      await usersService.createRole(payload);
      toast.add({ severity: 'success', summary: 'Rol Creado', detail: 'Nuevo rol registrado en el sistema', life: 3000 });
    }
    isRoleDialogVisible.value = false;
    await loadData();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al guardar rol', life: 4000 });
  } finally {
    isSavingRole.value = false;
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Administración de Usuarios y Roles</h2>
        <p class="text-xs text-slate-500">Gestión de cuentas, perfiles de seguridad RBAC y permisos por módulo</p>
      </div>
    </div>

    <!-- Main Tabs -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <Tabs value="0">
        <TabList>
          <Tab value="0">
            <i class="pi pi-users mr-1.5 text-blue-600"></i> Usuarios del Sistema ({{ filteredUsers.length }})
          </Tab>
          <Tab value="1">
            <i class="pi pi-shield mr-1.5 text-indigo-600"></i> Roles y Permisos RBAC ({{ roles.length }})
          </Tab>
        </TabList>

        <TabPanels>
          <!-- Tab 0: Usuarios -->
          <TabPanel value="0">
            <div class="p-4 space-y-4">
              <!-- Filtros de Usuarios -->
              <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div class="flex items-center space-x-2 flex-1 min-w-[240px] max-w-md">
                  <span class="p-input-icon-left w-full">
                    <i class="pi pi-search text-slate-400 text-xs"></i>
                    <InputText v-model="searchUser" placeholder="Buscar por usuario, nombre, email o rol..." class="w-full text-xs" />
                  </span>
                </div>

                <div class="flex items-center space-x-2">
                  <span class="text-xs font-semibold text-slate-500">Estado:</span>
                  <Dropdown
                    v-model="filterActiveStatus"
                    :options="[
                      { label: 'Todos los Usuarios', value: 'all' },
                      { label: 'Solo Activos', value: 'active' },
                      { label: 'Solo Inactivos', value: 'inactive' }
                    ]"
                    optionLabel="label"
                    optionValue="value"
                    class="text-xs w-44"
                    @change="loadData"
                  />
                  <Button
                    v-if="availableRolesForCreation.length > 0"
                    label="Nuevo Usuario"
                    icon="pi pi-user-plus"
                    size="small"
                    severity="primary"
                    @click="handleOpenCreateUser"
                  />
                </div>
              </div>

              <LoadingSpinner v-if="isLoading" message="Cargando usuarios..." />

              <div v-else-if="filteredUsers.length > 0">
                <DataTable :value="filteredUsers" responsiveLayout="scroll" stripedRows class="p-datatable-sm" rowHover>
                  <Column field="username" header="Usuario" sortable class="font-mono text-xs font-bold text-slate-800" />
                  <Column field="full_name" header="Nombre y Apellido" sortable class="font-semibold text-slate-800" />
                  <Column field="email" header="Correo Electrónico" sortable />
                  <Column header="Rol">
                    <template #body="{ data }">
                      <Tag :value="data.role?.name || 'Sin Rol'" severity="info" class="text-xs font-bold" />
                    </template>
                  </Column>
                  <Column header="Sucursal">
                    <template #body="{ data }">
                      <span class="text-xs text-slate-600">{{ data.sucursal?.nombre || 'Acceso Global (Todas)' }}</span>
                    </template>
                  </Column>
                  <Column header="Estado" style="width: 100px">
                    <template #body="{ data }">
                      <Tag :value="data.is_active ? 'Activo' : 'Inactivo'" :severity="data.is_active ? 'success' : 'danger'" class="text-xs font-bold" />
                    </template>
                  </Column>
                  <Column header="Acciones" style="width: 130px" alignFrozen="right" frozen>
                    <template #body="{ data }">
                      <div class="flex items-center space-x-1">
                        <!-- Reset Password (Solo Admin) -->
                        <Button
                          v-if="authStore.isAdmin"
                          icon="pi pi-key"
                          text
                          rounded
                          size="small"
                          severity="warn"
                          title="Restablecer contraseña (Admin)"
                          @click="handleOpenResetPassword(data)"
                        />
                        <!-- Editar Usuario (Solo Admin) -->
                        <Button
                          v-if="authStore.isAdmin"
                          icon="pi pi-pencil"
                          text
                          rounded
                          size="small"
                          severity="info"
                          title="Editar datos de usuario"
                          @click="handleOpenEditUser(data)"
                        />
                        <!-- Activar / Inactivar (Solo Admin) -->
                        <Button
                          v-if="authStore.isAdmin"
                          :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check'"
                          text
                          rounded
                          size="small"
                          :severity="data.is_active ? 'danger' : 'success'"
                          :title="data.is_active ? 'Inactivar usuario' : 'Activar usuario'"
                          @click="handleToggleActiveUser(data)"
                        />
                      </div>
                    </template>
                  </Column>
                </DataTable>
              </div>

              <EmptyState
                v-else
                title="No se encontraron usuarios"
                description="No hay cuentas que coincidan con el filtro seleccionado."
                icon="pi pi-users"
              />
            </div>
          </TabPanel>

          <!-- Tab 1: Roles y Permisos -->
          <TabPanel value="1">
            <div class="p-4 space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-sm font-bold text-slate-800">Catálogo de Roles y Permisos RBAC</h4>
                  <p class="text-xs text-slate-500">Configuración de perfiles y acceso granular a cada módulo</p>
                </div>
                <Button
                  v-if="authStore.isAdmin"
                  label="Nuevo Rol"
                  icon="pi pi-plus"
                  size="small"
                  severity="primary"
                  @click="handleOpenCreateRole"
                />
              </div>

              <DataTable :value="roles" responsiveLayout="scroll" class="p-datatable-sm" rowHover>
                <Column field="name" header="Nombre del Rol" sortable style="width: 220px">
                  <template #body="{ data }">
                    <div>
                      <span class="font-bold text-slate-800 text-xs">{{ data.name }}</span>
                      <span v-if="data.is_system" class="ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">Base</span>
                    </div>
                  </template>
                </Column>

                <Column field="code" header="Código" sortable style="width: 140px">
                  <template #body="{ data }">
                    <span class="font-mono text-xs text-slate-500 font-semibold">{{ data.code }}</span>
                  </template>
                </Column>

                <Column field="hierarchy_level" header="Nivel Jerárquico" sortable style="width: 130px">
                  <template #body="{ data }">
                    <span class="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-100 text-slate-700">
                      Nivel {{ data.hierarchy_level || 10 }}
                    </span>
                  </template>
                </Column>

                <Column field="description" header="Descripción" style="width: 220px">
                  <template #body="{ data }">
                    <span class="text-xs text-slate-600">{{ data.description || '-' }}</span>
                  </template>
                </Column>

                <Column header="Permisos Asignados">
                  <template #body="{ data }">
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="p in data.permissions"
                        :key="p.id"
                        class="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-blue-50 text-blue-700 border border-blue-200"
                        :title="p.description || p.code"
                      >
                        {{ p.code }}
                      </span>
                    </div>
                  </template>
                </Column>

                <Column v-if="authStore.isAdmin" header="Acciones" style="width: 80px">
                  <template #body="{ data }">
                    <Button
                      icon="pi pi-pencil"
                      text
                      rounded
                      size="small"
                      severity="info"
                      @click="handleOpenEditRole(data)"
                      title="Editar rol y permisos"
                    />
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>

    <!-- Dialog: Crear / Editar Usuario -->
    <Dialog
      v-model:visible="isUserDialogVisible"
      modal
      :header="isEditingUser ? `Editar Usuario: ${userForm.username}` : 'Registrar Nuevo Usuario'"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombre <span class="text-red-500">*</span></label>
            <InputText v-model="userForm.first_name" class="w-full text-xs" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Apellido <span class="text-red-500">*</span></label>
            <InputText v-model="userForm.last_name" class="w-full text-xs" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombre de Usuario <span class="text-red-500">*</span></label>
          <InputText
            v-model="userForm.username"
            class="w-full text-xs font-mono"
            placeholder="ej: jcarlos"
            :disabled="isEditingUser"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Correo Electrónico <span class="text-red-500">*</span></label>
          <InputText v-model="userForm.email" type="email" class="w-full text-xs" placeholder="usuario@correo.com" />
        </div>

        <div v-if="!isEditingUser">
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Contraseña Inicial <span class="text-red-500">*</span></label>
          <Password v-model="userForm.password" class="w-full" inputClass="w-full text-xs" :feedback="false" toggleMask />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Rol Asignado <span class="text-red-500">*</span></label>
            <Dropdown
              v-model="userForm.role_id"
              :options="availableRolesForCreation"
              optionLabel="name"
              optionValue="id"
              class="w-full text-xs"
              placeholder="Seleccionar rol..."
            />
            <p v-if="!authStore.isAdmin" class="text-[10px] text-slate-400 mt-0.5">
              * Solo puedes asignar roles de menor jerarquía a tu cuenta.
            </p>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Sucursal (Opcional)</label>
            <Dropdown v-model="userForm.sucursal_id" :options="sucursales" optionLabel="nombre" optionValue="id" placeholder="Todas las sucursales" showClear class="w-full text-xs" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isUserDialogVisible = false" />
        <Button
          :label="isEditingUser ? 'Guardar Cambios' : 'Registrar Usuario'"
          icon="pi pi-check"
          severity="primary"
          :loading="isSavingUser"
          @click="handleSaveUser"
        />
      </template>
    </Dialog>

    <!-- Dialog: Restablecer Contraseña por Admin -->
    <Dialog
      v-model:visible="isResetPasswordDialogVisible"
      modal
      :header="`Restablecer Contraseña: ${resetPasswordUsername}`"
      :style="{ width: '420px' }"
    >
      <div class="space-y-3">
        <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
          <i class="pi pi-info-circle text-amber-600 text-sm mt-0.5"></i>
          <p>Como Administrador puedes establecer una nueva contraseña directamente para este usuario si la ha olvidado.</p>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Nueva Contraseña <span class="text-red-500">*</span>
          </label>
          <Password
            v-model="newAdminPassword"
            class="w-full"
            inputClass="w-full text-xs"
            placeholder="Mínimo 6 caracteres"
            :feedback="false"
            toggleMask
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isResetPasswordDialogVisible = false" />
        <Button
          label="Establecer Contraseña"
          icon="pi pi-check"
          severity="warn"
          :loading="isSavingResetPassword"
          @click="handleSaveResetPassword"
        />
      </template>
    </Dialog>

    <!-- Dialog: Crear / Editar Rol con Permisos -->
    <Dialog
      v-model:visible="isRoleDialogVisible"
      modal
      :header="isEditingRole ? `Editar Rol: ${roleForm.name}` : 'Crear Nuevo Rol'"
      :style="{ width: '600px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Código del Rol <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="roleForm.code"
              placeholder="Ej: SUPERVISOR"
              class="w-full text-xs uppercase font-mono"
              :disabled="isEditingRole"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nombre Legible <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="roleForm.name"
              placeholder="Ej: Supervisor de Sucursal"
              class="w-full text-xs font-bold"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nivel Jerárquico <span class="text-red-500">*</span>
            </label>
            <Dropdown
              v-model="roleForm.hierarchy_level"
              :options="[
                { label: 'Nivel 100 - Administrador', value: 100 },
                { label: 'Nivel 50 - Auditor / Especialista', value: 50 },
                { label: 'Nivel 20 - Supervisor', value: 20 },
                { label: 'Nivel 10 - Operador / Sucursal', value: 10 },
                { label: 'Nivel 5 - Solo Consulta', value: 5 }
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full text-xs"
            />
            <p class="text-[10px] text-slate-400 mt-0.5">Define qué roles inferiores puede crear este usuario</p>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Descripción</label>
            <Textarea
              v-model="roleForm.description"
              rows="2"
              placeholder="Alcance del rol..."
              class="w-full text-xs"
            />
          </div>
        </div>

        <!-- Selector de Permisos Agrupados por Módulo -->
        <div class="pt-2 border-t border-slate-200 space-y-3">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-bold text-slate-800 uppercase">
              Permisos Asignados ({{ roleForm.permission_ids.length }} seleccionados)
            </label>
          </div>

          <div class="max-h-60 overflow-y-auto space-y-3 p-2 bg-slate-50 rounded-lg border border-slate-200">
            <div v-for="(perms, moduleName) in permissionsByModule" :key="moduleName" class="space-y-1.5">
              <span class="text-[11px] font-bold text-slate-700 uppercase tracking-wide px-1 block border-b border-slate-200 pb-0.5">
                Módulo: {{ moduleName }}
              </span>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pl-2">
                <div v-for="p in perms" :key="p.id" class="flex items-center space-x-2">
                  <Checkbox
                    v-model="roleForm.permission_ids"
                    :value="p.id"
                    :inputId="`perm_${p.id}`"
                  />
                  <label :for="`perm_${p.id}`" class="text-xs text-slate-700 cursor-pointer select-none">
                    <span class="font-mono text-[11px] font-semibold text-blue-800">{{ p.code }}</span>
                    <span v-if="p.description" class="block text-[10px] text-slate-400">{{ p.description }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isRoleDialogVisible = false" />
        <Button
          :label="isEditingRole ? 'Guardar Cambios' : 'Registrar Rol'"
          icon="pi pi-check"
          severity="primary"
          :loading="isSavingRole"
          @click="handleSaveRole"
        />
      </template>
    </Dialog>
  </div>
</template>

