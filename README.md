# ServiGo!! — V2

Aplicación web desarrollada con Django para conectar clientes con profesionales, facilitar la contratación de servicios y ofrecer un espacio comunitario para compartir preguntas y consejos sobre mantenimiento, reparaciones y mejoras del hogar.

La aplicación utiliza SQLite para la persistencia de datos y una interfaz web con Tailwind CSS.

## Funcionalidades

### Cuentas y perfiles
- Registro de usuarios e inicio y cierre de sesión.
- Perfil personal con nombre, correo electrónico, teléfono, dirección y fotografía.
- Cambio de contraseña.
- Roles de usuario, técnico y administrador.

### Técnicos profesionales
- Solicitud para convertirse en técnico.
- Envío de documentos PDF e imágenes.
- Revisión administrativa de las solicitudes.
- Estados de revisión, aprobación y rechazo.
- Retroalimentación para corregir y reenviar solicitudes.
- Restricción de las funciones profesionales hasta obtener la aprobación.

### Catálogo de servicios
- Exploración de los servicios disponibles.
- Búsqueda por texto.
- Filtros por categoría.
- Consulta de perfiles de técnicos aprobados.

### Solicitudes y cotizaciones
- Creación de solicitudes con descripción, dirección y fecha preferida.
- Adjuntos y evidencias de la solicitud.
- Envío de cotizaciones por técnicos aprobados.
- Revisión y aceptación de cotizaciones por parte del cliente.
- Asignación del técnico seleccionado.
- Seguimiento del estado del servicio.
- Reseñas y calificaciones de técnicos después de completar un servicio.

### Comunidad ServiGo!!
- Publicaciones organizadas por categorías.
- Búsqueda y filtrado de publicaciones.
- Creación de preguntas y consejos por parte de los usuarios.
- Respuestas a las publicaciones.
- Votos para identificar contenido útil.
- Reportes de contenido que requiere revisión.
- Moderación de publicaciones, respuestas y reportes.
- Publicaciones iniciales de demostración identificadas como tales.

Las publicaciones y respuestas nuevas pueden quedar pendientes de aprobación antes de hacerse visibles, según las reglas de moderación implementadas.

### Administración
- Gestión de usuarios y roles.
- Revisión de solicitudes para convertirse en técnico.
- Gestión de servicios y solicitudes.
- Administración y moderación de la comunidad.

## Tecnologías

- Python
- Django 5.2
- SQLite
- Pillow
- HTML y Tailwind CSS

## Requisitos previos

- Python compatible con Django 5.2.
- pip.
- Git, si se desea clonar el repositorio.

## Instalación limpia en Windows PowerShell

Desde la carpeta del proyecto que contiene `manage.py`, ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Aplica las migraciones del proyecto:

```powershell
python manage.py migrate
```

Crea una cuenta de administrador:

```powershell
python manage.py createsuperuser
```

Comprueba la configuración e inicia el servidor:

```powershell
python manage.py check
python manage.py runserver
```

Abre la aplicación en:

- Inicio: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/catalog/
- Comunidad: http://127.0.0.1:8000/comunidad/
- Solicitudes: http://127.0.0.1:8000/solicitudes/
- Administración: http://127.0.0.1:8000/admin/

## Instalación en un entorno existente

Si ya tienes una instalación con datos, activa el entorno virtual correspondiente e instala las dependencias:

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Antes de actualizar, realiza una copia de seguridad de `db.sqlite3`, `media/` y de los archivos de migración relevantes.

No elimines la base de datos ni las migraciones existentes para resolver errores. Revisa primero el estado de las migraciones.

## Preparar la comunidad

La aplicación incluye un comando para crear categorías y publicaciones iniciales de demostración:

```powershell
python manage.py seed_community
```

Ejecuta este comando después de aplicar las migraciones y crear al menos una cuenta administradora.

El comando puede ejecutarse nuevamente para comprobar si existen publicaciones iniciales; las publicaciones que ya existen no deberían duplicarse.

## URLs principales

| Ruta | Función |
|---|---|
| `/` | Página de inicio |
| `/accounts/registro/` | Registro |
| `/accounts/login/` | Inicio de sesión |
| `/accounts/perfil/` | Perfil personal |
| `/accounts/cambiar-password/` | Cambio de contraseña |
| `/technicians/solicitud/` | Solicitud para ser técnico |
| `/technicians/solicitud/estado/` | Estado de la solicitud técnica |
| `/catalog/` | Catálogo de servicios |
| `/solicitudes/` | Listado de solicitudes |
| `/solicitudes/nueva/` | Crear una solicitud de servicio |
| `/comunidad/` | Comunidad ServiGo!! |
| `/comunidad/nueva/` | Crear una publicación |
| `/comunidad/moderacion/` | Moderación de la comunidad |
| `/admin/` | Administración de Django |

Las rutas pueden variar si se modifican las configuraciones de URL del proyecto.

## Flujo de los servicios

1. Una persona se registra con el rol de usuario.
2. Desde su perfil puede solicitar convertirse en técnico.
3. La solicitud técnica pasa por revisión administrativa.
4. Los técnicos aprobados pueden acceder a las funciones profesionales disponibles.
5. El cliente crea una solicitud de servicio y proporciona la información necesaria.
6. Los técnicos aprobados presentan sus cotizaciones.
7. El cliente selecciona una cotización y se asigna el técnico correspondiente.
8. El servicio avanza por los estados permitidos hasta su finalización.
9. El cliente puede calificar al técnico una vez completado el servicio.

## Flujo de la comunidad

1. Los usuarios consultan las publicaciones aprobadas.
2. Los usuarios autenticados pueden crear publicaciones y responder.
3. Las publicaciones y respuestas nuevas se someten a revisión cuando así lo establece la aplicación.
4. Los usuarios pueden votar por contenido útil y reportar publicaciones.
5. Los moderadores revisan el contenido pendiente y los reportes.
6. Las publicaciones iniciales de demostración se identifican mediante el campo `is_seed`.

## Archivos y almacenamiento

- `db.sqlite3`: base de datos local de desarrollo.
- `media/`: archivos subidos por los usuarios.
- `static/`: recursos estáticos del proyecto, si corresponde.
- `requirements.txt`: dependencias de Python.
- `manage.py`: herramienta de administración de Django.

Las carpetas de migraciones de cada aplicación deben conservarse en el repositorio.

## Seguridad y despliegue

La configuración local está destinada al desarrollo y las pruebas.

Antes de publicar la aplicación en internet:

- Configura `DEBUG = False`.
- Establece `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` según el dominio utilizado.
- Guarda `SECRET_KEY` y otras credenciales en variables de entorno.
- Configura HTTPS y un servidor de despliegue adecuado.
- Revisa los permisos de acceso a documentos, evidencias y fotografías.
- Configura almacenamiento persistente y copias de seguridad.
- No publiques bases de datos con información personal ni documentos privados.

El servidor de desarrollo de Django no debe utilizarse como servidor de producción.

## Estado del proyecto

ServiGo!! V2 integra cuentas, perfiles profesionales, catálogo de servicios, solicitudes, cotizaciones y una comunidad con herramientas de moderación.
