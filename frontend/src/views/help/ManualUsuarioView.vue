<script setup lang="ts">
import { ref, computed } from 'vue';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Tag from 'primevue/tag';

const searchQuery = ref('');
const activeChapter = ref('cap1');

const handlePrint = () => {
  if (typeof window !== 'undefined') {
    window.print();
  }
};

const chapters = [
  { id: 'cap1', title: '1. Acceso y Primeros Pasos', icon: 'pi pi-key' },
  { id: 'cap2', title: '2. Padrón de Pacientes y Mutuales', icon: 'pi pi-users' },
  { id: 'cap3', title: '3. Registro de Órdenes Médicas', icon: 'pi pi-plus-circle' },
  { id: 'cap4', title: '4. Expediente Clínico y Visor', icon: 'pi pi-folder-open' },
  { id: 'cap5', title: '5. Ciclo de Auditoría y Estados', icon: 'pi pi-sync' },
  { id: 'cap6', title: '6. Bandeja de Llamadas a Pacientes', icon: 'pi pi-phone' },
  { id: 'cap7', title: '7. Dashboard y Reportes Excel', icon: 'pi pi-chart-line' },
  { id: 'cap8', title: '8. Usuarios, Roles y Seguridad', icon: 'pi pi-shield' },
  { id: 'cap9', title: '9. Integraciones API y n8n', icon: 'pi pi-code' },
];

const filteredChapters = computed(() => {
  if (!searchQuery.value.trim()) return chapters;
  const q = searchQuery.value.toLowerCase();
  return chapters.filter((c) => c.title.toLowerCase().includes(q));
});

const scrollToChapter = (id: string) => {
  activeChapter.value = id;
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};
</script>

<template>
  <div class="space-y-6 pb-12">
    <!-- Header -->
    <div
      class="bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white p-6 rounded-2xl shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span
            class="px-2.5 py-0.5 rounded-full bg-blue-700/80 text-blue-100 text-xs font-semibold tracking-wider uppercase">
            Guía Oficial de Usuario &bull; Versión 1.3
          </span>
        </div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight">Manual de Uso del Sistema</h1>
        <p class="text-blue-100 text-sm mt-1 max-w-2xl">
          Instrucciones operativas, flujos de auditoría médica, registro de llamadas telefónicas y guía paso a paso para
          operadores, auditores y administradores.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <a href="/docs" target="_blank">
          <Button label="API Swagger Docs" icon="pi pi-external-link" severity="info" size="small"
            class="bg-blue-600 hover:bg-blue-500 border-none text-xs" />
        </a>
        <Button label="Imprimir / Guardar PDF" icon="pi pi-print" severity="secondary" size="small"
          class="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs" @click="handlePrint" />
      </div>
    </div>

    <!-- Main Content Layout -->
    <div class="grid grid-cols-12 gap-6 items-start">
      <!-- Navigation Sidebar -->
      <div class="col-span-12 lg:col-span-4 sticky top-4 space-y-4">
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <i class="pi pi-list text-blue-600"></i> Tabla de Contenidos
          </h3>
          <span class="p-input-icon-left w-full">
            <i class="pi pi-search text-slate-400 text-xs"></i>
            <InputText v-model="searchQuery" placeholder="Buscar en el manual..." class="w-full text-xs" />
          </span>

          <nav class="space-y-1">
            <button v-for="ch in filteredChapters" :key="ch.id"
              class="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition"
              :class="activeChapter === ch.id ? 'bg-blue-50 text-blue-800 border-l-4 border-blue-600' : 'text-slate-600 hover:bg-slate-50'"
              @click="scrollToChapter(ch.id)">
              <i :class="[ch.icon, activeChapter === ch.id ? 'text-blue-600' : 'text-slate-400']"></i>
              <span>{{ ch.title }}</span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Chapter Content -->
      <div class="col-span-12 lg:col-span-8 space-y-6">
        <!-- Content sections will be rendered here -->
        <div id="cap1" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-key text-blue-600"></i>
              <span>1. Acceso y Primeros Pasos</span>
            </h2>
            <Tag value="General" severity="info" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El <strong>Sistema de Gestión de Órdenes Médicas</strong> es una aplicación web accesible desde cualquier
              navegador moderno (Google Chrome, Microsoft Edge, Safari o Firefox).
            </p>
            <div class="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-2">
              <p class="font-bold text-slate-800 text-xs">Para iniciar sesión:</p>
              <ol class="list-decimal list-inside space-y-1 text-slate-600">
                <li>Ingrese a la dirección web del sistema: <code>https://auditorias.jmob.ar</code> (o
                  <code>http://localhost:5173</code> en desarrollo local).</li>
                <li>Escriba su <strong>Nombre de Usuario</strong> o su <strong>Correo Electrónico</strong> registrado.
                </li>
                <li>Ingrese su <strong>Contraseña</strong> personal y presione <strong>Iniciar Sesión</strong>.</li>
              </ol>
            </div>
            <p>
              Una vez dentro, el menú lateral izquierdo le permitirá navegar entre los módulos autorizados según su
              nivel de permisos (Operador de Sucursal, Auditor Médico o Administrador General).
            </p>
          </div>
        </div>

        <div id="cap2" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-users text-blue-600"></i>
              <span>2. Padrón de Pacientes y Obras Sociales</span>
            </h2>
            <Tag value="Pacientes" severity="success" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El módulo de <strong>Pacientes</strong> almacena los datos de filiación, documento de identidad (DNI),
              fecha de nacimiento, Obra Social y datos de contacto directo (teléfono, celular y correo).
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="p-3 bg-blue-50/70 border border-blue-200 rounded-lg">
                <p class="font-bold text-blue-900 mb-1"><i class="pi pi-id-card mr-1"></i> Alta de Pacientes con Validación Estricta</p>
                <p class="text-slate-600">
                  Para garantizar la calidad de los registros clínicos, son <strong>obligatorios</strong>: DNI/Documento, Nombres, Apellidos y <strong>Fecha de Nacimiento</strong>.
                </p>
              </div>
              <div class="p-3 bg-indigo-50/70 border border-indigo-200 rounded-lg">
                <p class="font-bold text-indigo-900 mb-1"><i class="pi pi-building mr-1"></i> Mutuales y Copago por Defecto</p>
                <p class="text-slate-600">
                  En el menú de <strong>Obras Sociales</strong> puede configurar los días de validez de las órdenes y el <strong>Copago Predeterminado ($)</strong> para que se cargue automáticamente al emitir una orden.
                </p>
              </div>
            </div>
          </div>
        </div>
        <!-- Capítulo 3: Registro de Órdenes Médicas -->
        <div id="cap3" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-plus-circle text-blue-600"></i>
              <span>3. Registro y Carga de Órdenes Médicas</span>
            </h2>
            <Tag value="Operadores" severity="primary" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              Para registrar una nueva prescripción médica, acceda a <strong>Nueva Orden</strong> en el menú lateral. El
              formulario se divide en 3 secciones estructuradas:
            </p>
            <div class="space-y-3">
              <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <p class="font-bold text-slate-900">Paso 1: Selección del Paciente</p>
                <p class="text-slate-600">Busque al paciente por DNI o Nombre en el campo autocompletable. Si el
                  paciente es nuevo, presione el botón <strong>"+ Nuevo Paciente"</strong> para crearlo al instante sin
                  salir del formulario.</p>
                <p class="text-slate-600 font-semibold text-blue-800">💡 Al seleccionar al paciente, el sistema
                  autocompleta automáticamente su Obra Social, su N° de Afiliado y sus teléfonos de contacto.</p>
              </div>

              <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <p class="font-bold text-slate-900">Paso 2: Prescripción, Mutual, Copago y APB</p>
                <ul class="list-disc list-inside space-y-1 text-slate-600">
                  <li><strong>Fecha de Prescripción (*):</strong> Fecha en que el médico emitió la receta. Al seleccionarla, el sistema calcula automáticamente la <strong>Fecha de Vencimiento</strong> según la mutual.</li>
                  <li><strong>Mutual / Cobertura (*):</strong> Al elegir la obra social, el campo <strong>Valor Copago</strong> se completa automáticamente con el valor sugerido, manteniéndose editable.</li>
                  <li><strong>N° Afiliado / Credencial (*):</strong> Número de afiliado obligatorio para validación ante la mutual.</li>
                  <li><strong>Cantidad de Recetas Físicas (*):</strong> Debe ser mayor a 0.</li>
                  <li><strong>🧪 Checkbox Abona APB (Acto Profesional Bioquímico):</strong> Active esta opción si la orden requiere cobro de arancel por APB según convenio.</li>
                  <li><strong>⚠️ Checkbox Paciente Debe Orden Médica Física:</strong> Active esta casilla si la orden fue recibida digitalmente (mail/WhatsApp) para exigir la receta física el día del estudio.</li>
                </ul>
              </div>

              <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <p class="font-bold text-slate-900">Paso 3: Contacto y Notificaciones</p>
                <p class="text-slate-600">Son obligatorios el <strong>Nombre de Contacto</strong>, el <strong>Horario Preferido</strong> y al menos un número de comunicación (<strong>Teléfono Fijo o Celular/WhatsApp</strong>).</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Capítulo 4: Expediente Clínico y Visor -->
        <div id="cap4" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-folder-open text-blue-600"></i>
              <span>4. Gestión y Expediente Clínico de Órdenes</span>
            </h2>
            <Tag value="Expediente" severity="warn" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El listado de <strong>Órdenes Médicas</strong> cuenta con una interfaz <strong>Master-Detail (Vista
                Dividida)</strong> que permite revisar expedientes sin recargar la pantalla:
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900"><i class="pi pi-eye mr-1 text-blue-600"></i> Selección Rápida y
                  Pantalla Completa</p>
                <p class="text-slate-600">Haga clic en cualquier fila para desplegar el expediente en el panel lateral
                  derecho, o presione el botón de <strong>Pantalla Completa</strong> para ver el
                  expediente extendido.</p>
              </div>
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900"><i class="pi pi-file mr-1 text-blue-600"></i> Visor Popup de Fotos y
                  PDFs</p>
                <p class="text-slate-600">En la pestaña de <strong>Adjuntos</strong>, haga clic en cualquier receta
                  escaneada o foto para abrir el visor emergente integrado sin necesidad de descargar el archivo.</p>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="p-3 bg-blue-50/70 border border-blue-200 rounded-lg space-y-1">
                <p class="font-bold text-blue-900"><i class="pi pi-tags mr-1"></i> Códigos de Autorización</p>
                <p class="text-slate-600">Puede cargar múltiples números de autorización individualmente con el botón
                  <strong>+</strong> y eliminarlos uno a uno. Al cargarlos, la orden pasa automáticamente a estado <em>en Auditoria</em>.</p>
              </div>
              <div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg space-y-1">
                <p class="font-bold text-emerald-900"><i class="pi pi-phone mr-1"></i> Registro Directo de Llamadas</p>
                <p class="text-slate-600">En la pestaña <strong>Llamadas</strong>, el botón <strong>+ Registrar Llamada</strong> permite asentar consultas recibidas del paciente o gestiones internas, con opción de resolver avisos pendientes al vuelo.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Capítulo 5: Ciclo de Auditoría y Estados -->
        <div id="cap5" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-sync text-blue-600"></i>
              <span>5. Ciclo de Auditoría Médica y Transición de Estados</span>
            </h2>
            <Tag value="Auditoría" severity="contrast" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El sistema distingue entre dos tipos de observaciones médicas emitidas por los auditores:
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
              <div class="p-3 bg-amber-50 border border-amber-300 rounded-lg space-y-1">
                <p class="font-bold text-amber-900 flex items-center gap-1">
                  <i class="pi pi-exclamation-triangle text-amber-600"></i> Solicitud de Auditoría (Ámbar)
                </p>
                <p class="text-slate-600">
                  Requiere documentación o aclaración obligatoria. <strong>Pasa la orden a 'Solicitudes de auditoria' e ingresa a la Bandeja de Llamadas</strong> para avisar al paciente.
                </p>
              </div>
              <div class="p-3 bg-blue-50 border border-blue-300 rounded-lg space-y-1">
                <p class="font-bold text-blue-900 flex items-center gap-1">
                  <i class="pi pi-info-circle text-blue-600"></i> Solo Información (Azul)
                </p>
                <p class="text-slate-600">
                  Nota técnica o aclaración interna. Queda identificada con badge azul <code>INFORMACIÓN</code>, <strong>no altera el estado de la orden y no genera llamadas pendientes</strong>.
                </p>
              </div>
            </div>
            <p class="font-bold text-slate-800 pt-1">Ciclo de vida completo:</p>
            <div class="space-y-2">
              <div class="p-2.5 bg-blue-50/60 rounded border border-blue-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">1. Ingreso</span>
                <p class="text-slate-600">Orden recibida en sucursal esperando asignación o revisión.</p>
              </div>
              <div class="p-2.5 bg-amber-50/60 rounded border border-amber-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">2. en
                  Auditoria</span>
                <p class="text-slate-600">El auditor médico está evaluando la prescripción o gestionando códigos de
                  autorización.</p>
              </div>
              <div class="p-2.5 bg-red-50/60 rounded border border-red-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">3. Solicitudes de
                  auditoria</span>
                <p class="text-slate-600">El auditor emitió una observación clínica. <strong>Entra en la Bandeja de Llamadas para notificar al paciente.</strong></p>
              </div>
              <div class="p-2.5 bg-slate-100 rounded border border-slate-300 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800">4.
                  Actualizada</span>
                <p class="text-slate-600">La sucursal respondió la observación o adjuntó nueva documentación para
                  re-evaluación médica.</p>
              </div>
              <div class="p-2.5 bg-indigo-50/60 rounded border border-indigo-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800">5. Auditoria
                  Finalizada</span>
                <p class="text-slate-600">Auditoría aprobada y resuelta con observación de resultado. <strong>Entra en la Bandeja de Llamadas para confirmar la atención al paciente.</strong></p>
              </div>
              <div class="p-2.5 bg-emerald-50/60 rounded border border-emerald-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">6. Cerrada
                  (Terminal)</span>
                <p class="text-slate-600">Resolución exitosa: el paciente se presentó en sede y se completó la atención.</p>
              </div>
              <div class="p-2.5 bg-rose-50/60 rounded border border-rose-200 flex items-start gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">7. Cancelada / Dar de
                  Baja (Terminal)</span>
                <p class="text-slate-600">Rechazo o anulación de la orden con motivo formal obligatorio.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Capítulo 6: Bandeja de Llamadas a Pacientes -->
        <div id="cap6" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-phone text-blue-600"></i>
              <span>6. Bandeja de Llamadas a Pacientes y Call Center</span>
            </h2>
            <Tag value="Recepción / Call Center" severity="danger" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              La <strong>Bandeja de Llamadas</strong> lista exclusivamente a aquellos pacientes que requieren ser
              contactados de forma prioritaria:
            </p>
            <div class="space-y-2">
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900">📌 Regla de Oro y Resolución Automática de Avisos:</p>
                <p class="text-slate-600">
                  Al registrar una llamada con resultado <strong>EXITOSA</strong>, la orden se quita inmediatamente de
                  la bandeja de pendientes, pero <strong>NO altera el estado del ciclo de vida de la orden</strong>.
                </p>
                <p class="text-blue-800 font-semibold text-xs mt-1">
                  📞 Si el paciente se comunica espontáneamente con la sucursal (Consulta Entrante), el operador puede registrar la llamada desde el expediente y marcar <em>"Dar por comunicado el aviso"</em> para sacarla de pendientes de forma inmediata.
                </p>
              </div>
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900">💬 Modal Popup de Observaciones:</p>
                <p class="text-slate-600">
                  El operador puede hacer clic en el botón de observaciones para leer en una ventana emergente el motivo
                  exacto indicado por el auditor médico o la resolución final a comunicarle al paciente.
                </p>
              </div>
              <div class="p-3 bg-red-50/70 border border-red-200 rounded-lg space-y-1">
                <p class="font-bold text-red-900">⚠️ Cobro y Deuda de Receta Física:</p>
                <p class="text-slate-600">
                  En la misma fila y en el modal de llamadas se detalla el <strong>Total a Cobrar</strong> (Bono + No
                  Autorizados) y el aviso en rojo si el paciente <strong>DEBE la receta física original</strong> para
                  recordarle que debe presentarla el día de la toma de muestra.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Capítulo 7: Dashboard y Reportes Excel -->
        <div id="cap7" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-chart-line text-blue-600"></i>
              <span>7. Dashboard Ejecutivo y Exportación a Excel</span>
            </h2>
            <Tag value="Métricas" severity="info" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El <strong>Dashboard</strong> consolida indicadores en tiempo real para la toma de decisiones clínicas y
              directivas:
            </p>
            <ul class="list-disc list-inside space-y-1 text-slate-600">
              <li><strong>Tarjetas de KPIs:</strong> Total de órdenes históricas, órdenes activas en curso, órdenes en
                auditoría médica, tasa de efectividad (% de órdenes cerradas exitosamente) y total recaudado de copagos.
              </li>
              <li><strong>Gráficos Analíticos:</strong> Distribución porcentual por estado del ciclo de vida y
                comparativa de órdenes abiertas vs cerradas por cada sucursal.</li>
              <li><strong>Exportar a Excel (CSV):</strong> Botón superior que descarga de inmediato la base completa de
                órdenes con codificación <em>UTF-8 BOM</em> para compatibilidad nativa con Microsoft Excel sin
                caracteres extraños.</li>
            </ul>
          </div>
        </div>

        <!-- Capítulo 8: Usuarios, Roles y Seguridad -->
        <div id="cap8" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-shield text-blue-600"></i>
              <span>8. Gestión de Usuarios, Roles Jerárquicos y Seguridad</span>
            </h2>
            <Tag value="Administración" severity="warn" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              Módulo exclusivo para administradores y supervisores:
            </p>
            <div class="space-y-2">
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900">👑 Jerarquía de Roles (*hierarchy_level*):</p>
                <p class="text-slate-600">Cada rol posee un nivel numérico de jerarquía (ej: Admin = 100, Supervisor =
                  50, Operador = 10). Un usuario únicamente puede crear, editar o asignar usuarios con nivel jerárquico
                  inferior al suyo.</p>
              </div>
              <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <p class="font-bold text-slate-900">🔑 Cambio y Reseteo Seguro de Contraseñas:</p>
                <p class="text-slate-600">En la tabla de usuarios, el botón de la llave permite restablecer de forma
                  directa la contraseña de cualquier usuario del equipo con confirmación inmediata.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Capítulo 9: Integraciones API y n8n -->
        <div id="cap9" class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div class="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-code text-blue-600"></i>
              <span>9. Documentación de API Swagger (`/docs`) y Automatizaciones con n8n</span>
            </h2>
            <Tag value="Desarrollo / n8n" severity="secondary" />
          </div>
          <div class="text-xs text-slate-700 leading-relaxed space-y-3">
            <p>
              El sistema dispone de una API REST moderna y documentada mediante **OpenAPI / Swagger UI**:
            </p>
            <div class="p-3 bg-slate-900 text-slate-200 rounded-lg font-mono text-[11px] space-y-1">
              <p class="text-emerald-400"># Documentación interactiva Swagger:</p>
              <p>URL: <a href="/docs" target="_blank"
                  class="underline text-blue-400">https://auditorias.jmob.ar/docs</a></p>
              <p class="text-slate-400 mt-2"># Integración con n8n:</p>
              <p>Autenticación: Bearer &lt;access_token&gt; generado en POST /api/v1/auth/login</p>
              <p>Filtros por ID de estado numérico (1 a 8) compatibles para disparadores de WhatsApp y mail automático.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
