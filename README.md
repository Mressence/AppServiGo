# AppServiGo!! — V2

Aplicación web Django para conectar clientes con profesionales, con interfaz Tailwind CSS y persistencia en SQLite.

## Incluye

- Registro, inicio/cierre de sesión y perfil de cuenta.
- Perfil personal con nombre, correo, teléfono, dirección, foto y cambio de contraseña.
- Solicitud para convertirse en técnico con documentos PDF/imágenes, revisión administrativa, bloqueo durante revisión y retroalimentación para corregir y reenviar.
- Catálogo de servicios con búsqueda por texto y filtro por categoría.
- Solicitudes de servicio con descripción, dirección, fecha preferida y adjuntos/evidencias.
- Cotizaciones de técnicos aprobados, comparación y aceptación por el cliente.
- Reglas de transición: Pendiente → Cotizada → Aceptada → Programada → En ejecución → Completada; cancelación permitida antes de aceptar una cotización.
- Paneles y enlaces conectados a las páginas de solicitudes, perfil, catálogo y administración.
- SQLite en `db.sqlite3`; archivos subidos en `media/`.

## Instalación limpia (Windows PowerShell)

Desde la carpeta que contiene `manage.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations accounts technicians catalog service_requests
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. Administración: `http://127.0.0.1:8000/admin/`.

### Si usas Anaconda

Activa tu entorno donde ya tienes Python y después ejecuta:

```powershell
python -m pip install -r requirements.txt
python manage.py makemigrations accounts technicians catalog service_requests
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## URLs

- `/` — Inicio
- `/accounts/registro/` — Crear cuenta
- `/accounts/login/` — Iniciar sesión
- `/accounts/dashboard/` — Panel
- `/accounts/perfil/` — Perfil personal
- `/accounts/cambiar-password/` — Cambiar contraseña
- `/technicians/solicitud/` — Enviar/corregir solicitud para ser técnico
- `/technicians/solicitud/estado/` — Estado y retroalimentación de la solicitud técnica
- `/catalog/` — Catálogo con búsqueda y filtros
- `/solicitudes/` — Mis solicitudes o solicitudes disponibles para técnicos aprobados
- `/solicitudes/nueva/` — Crear solicitud de servicio
- `/admin/` — Administración

## Reglas del flujo

1. Una cuenta nueva se registra como Usuario.
2. Desde Mi perfil, la persona puede enviar la solicitud para convertirse en técnico.
3. La solicitud técnica queda bloqueada mientras está pendiente. Si se rechaza, se muestra la retroalimentación y se permite corregir y reenviar.
4. Al aprobar la solicitud en administración, el rol cambia automáticamente a Técnico. Solo técnicos aprobados pueden cotizar.
5. El cliente crea una solicitud y puede adjuntar archivos PDF/imágenes de hasta 10 MB cada uno.
6. Los técnicos aprobados envían cotizaciones. El cliente elige una; al aceptarla, el técnico queda asignado y las demás cotizaciones se marcan como no seleccionadas.
7. El técnico asignado (o un administrador) avanza el servicio por las transiciones permitidas. El cliente puede cancelar mientras la solicitud esté pendiente o cotizada.

## Nota sobre una instalación existente

Antes de reemplazar archivos en una instalación que ya tiene datos, haz una copia de `db.sqlite3`, `media/` y de las carpetas de migraciones. No borres `db.sqlite3`. Ejecuta `python manage.py makemigrations` y `python manage.py migrate` usando los archivos reales de tu proyecto. Si Django informa que una migración inicial ya existe o que una tabla ya existe, detente y revisa las migraciones locales antes de borrar nada.

## Límites de archivos

La aplicación acepta PDF, JPG, JPEG, PNG y WEBP para documentos/evidencias, con un límite de 10 MB por archivo. La entrega usa `MEDIA_ROOT` local para desarrollo. Para publicar en internet se debe configurar almacenamiento y permisos de archivos privados adecuados.
