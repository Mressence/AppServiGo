# AppServiGo!!

Proyecto web de **ServiGo!!**, desarrollado con Django para la gestión de usuarios, técnicos y servicios profesionales.

La versión actual corresponde a la primera etapa funcional del proyecto y establece la estructura base de autenticación, perfiles de usuario, roles, solicitudes de técnicos, aprobación administrativa y catálogo de servicios.

---

## Incluye

1. Registro y autenticación de usuarios.
2. Inicio y cierre de sesión.
3. Tres roles: Usuario, Técnico y Administrador.
4. Perfil de usuario editable.
5. Foto de perfil.
6. Cambio de contraseña.
7. Solicitud para convertirse en técnico.
8. Perfil profesional de técnicos.
9. Carga de documentación para solicitudes de técnicos.
10. Estados de solicitud: Pendiente, Aprobado y Rechazado.
11. Aprobación y rechazo de técnicos desde Django Admin.
12. Catálogo de categorías.
13. Catálogo de tipos de servicio.
14. Panel administrativo de Django.
15. Persistencia de información mediante SQLite.
16. Almacenamiento de imágenes y documentos mediante `media/`.
17. Frontend desarrollado con Django Templates.
18. Tailwind CSS mediante CDN.
19. Diseño responsive y mobile-first.
20. Navbar y footer reutilizables mediante templates parciales.
21. Arquitectura separada por aplicaciones Django.
22. Preparación para incorporar nuevas etapas y módulos de negocio.

---

## Tecnologías utilizadas

- Python 3.11+
- Django 5.2+
- SQLite
- Pillow
- Django Templates
- Tailwind CSS
- HTML5
- CSS
- JavaScript
- Cloudflare Tunnel para demostraciones temporales

---

## Requisitos

Antes de instalar el proyecto se recomienda contar con:

- Python 3.11 o superior.
- `pip`.
- Windows PowerShell si se trabaja en Windows.
- Entorno virtual de Python o Anaconda.

Para la funcionalidad de imágenes de perfil se utiliza **Pillow**.

---

## Instalación

### Windows PowerShell

Entrar a la carpeta del proyecto:

```powershell
cd AppServiGo
```

Crear el entorno virtual:

```powershell
python -m venv .venv
```

Activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar pip:

```powershell
python -m pip install --upgrade pip
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Aplicar las migraciones:

```powershell
python manage.py migrate
```

Crear el usuario administrador:

```powershell
python manage.py createsuperuser
```

Iniciar el servidor:

```powershell
python manage.py runserver
```

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

---

## Instalación utilizando Anaconda

Crear el entorno:

```powershell
conda create -n servigo python=3.13
```

Activar el entorno:

```powershell
conda activate servigo
```

Entrar al proyecto:

```powershell
cd AppServiGo
```

Instalar las dependencias:

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.txt
```

Aplicar las migraciones:

```powershell
python manage.py migrate
```

Crear el administrador:

```powershell
python manage.py createsuperuser
```

Ejecutar el servidor:

```powershell
python manage.py runserver
```

---

# Estructura del proyecto

La estructura principal del proyecto es:

```text
AppServiGo/
│
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── technicians/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── catalog/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
│   ├── accounts/
│   │   ├── change_password.html
│   │   ├── dashboard.html
│   │   └── profile.html
│   │
│   ├── technicians/
│   │   ├── application.html
│   │   └── application_status.html
│   │
│   ├── partials/
│   │   ├── footer.html
│   │   └── navbar.html
│   │
│   ├── base.html
│   └── home.html
│
├── static/
│   └── css/
│       └── app.css
│
├── media/
│   ├── profile_photos/
│   └── technician_documents/
│
├── db.sqlite3
├── manage.py
├── requirements.txt
└── README.md
```

---

# Aplicaciones Django

## `accounts`

Gestiona:

- Usuarios.
- Registro.
- Inicio de sesión.
- Cierre de sesión.
- Roles.
- Perfil de usuario.
- Foto de perfil.
- Cambio de contraseña.
- Dashboard.

---

## `technicians`

Gestiona:

- Solicitudes para convertirse en técnico.
- Información profesional.
- Experiencia.
- Documentación.
- Estado de aprobación.
- Rechazo y corrección de solicitudes.

---

## `catalog`

Gestiona:

- Categorías.
- Tipos de servicio.
- Visualización del catálogo.

El catálogo se encuentra preparado para ampliarse con nuevas características en futuras etapas.

---

# Roles

El sistema utiliza tres roles principales:

### Usuario

Es el rol asignado por defecto a las cuentas registradas.

Puede:

- Crear una cuenta.
- Iniciar sesión.
- Administrar su perfil.
- Cambiar su contraseña.
- Consultar el catálogo.
- Solicitar convertirse en técnico.

---

### Técnico

Es un usuario cuya solicitud para prestar servicios profesionales ha sido aprobada por un administrador.

Puede acceder a las funcionalidades correspondientes a técnicos que se incorporen al sistema.

---

### Administrador

Permite gestionar internamente la plataforma mediante Django Admin.

Puede:

- Administrar usuarios.
- Revisar solicitudes de técnicos.
- Aprobar técnicos.
- Rechazar solicitudes.
- Administrar categorías.
- Administrar tipos de servicio.
- Gestionar información del sistema.

---

# Registro y autenticación

Los usuarios pueden registrarse desde:

```text
/accounts/registro/
```

El inicio de sesión se encuentra en:

```text
/accounts/login/
```

El panel principal de un usuario autenticado se encuentra en:

```text
/accounts/dashboard/
```

El cierre de sesión se encuentra disponible desde la navegación principal.

---

# Perfil de usuario

Los usuarios autenticados pueden acceder a:

```text
/accounts/perfil/
```

Desde esta sección pueden modificar:

- Nombre.
- Apellido.
- Correo electrónico.
- Teléfono.
- Dirección.
- Foto de perfil.

La foto de perfil se almacena dentro de:

```text
media/profile_photos/
```

---

# Cambio de contraseña

El usuario puede cambiar su contraseña desde:

```text
/accounts/cambiar-password/
```

La funcionalidad utiliza las vistas de autenticación proporcionadas por Django.

---

# Solicitud para ser técnico

Un usuario puede iniciar el proceso para convertirse en técnico desde:

```text
/technicians/solicitud/
```

La solicitud permite registrar:

- Título profesional.
- Descripción profesional.
- Años de experiencia.
- Teléfono.
- Documento de identidad.
- Documento profesional.
- Documento adicional.

Los documentos se almacenan dentro de:

```text
media/technician_documents/
```

---

# Estados de las solicitudes de técnico

Las solicitudes utilizan tres estados:

```text
PENDIENTE
APROBADO
RECHAZADO
```

## Pendiente

La solicitud fue enviada y está esperando revisión administrativa.

Mientras se encuentra pendiente, la información de la solicitud no debe modificarse desde el flujo normal del usuario.

---

## Aprobado

Cuando el administrador aprueba la solicitud:

- El estado pasa a `APROBADO`.
- El usuario pasa a tener el rol `Técnico`.
- La solicitud queda aprobada.

---

## Rechazado

Cuando el administrador rechaza una solicitud:

- El estado pasa a `RECHAZADO`.
- El usuario conserva el rol `Usuario`.
- El usuario puede corregir la información correspondiente y volver a enviar la solicitud.

---

# Flujo del técnico

El flujo general es:

```text
Registro de usuario
        ↓
Usuario
        ↓
Solicitud para ser técnico
        ↓
Solicitud pendiente
        ↓
Revisión administrativa
        ↓
   ┌───────────────┐
   │               │
APROBADO        RECHAZADO
   │               │
   ↓               ↓
Técnico         Usuario
                corrige
                y reenvía
```

La revisión se realiza desde:

```text
/admin/
```

---

# Catálogo

El catálogo está disponible desde:

```text
/catalog/
```

Actualmente permite trabajar con:

- Categorías.
- Tipos de servicio.

El catálogo está diseñado para crecer posteriormente y relacionarse con los servicios profesionales ofrecidos por los técnicos.

---

# Panel administrativo

El panel administrativo de Django está disponible en:

```text
/admin/
```

El administrador puede utilizarlo para gestionar la información interna de la plataforma.

Entre los elementos administrables se encuentran:

- Usuarios.
- Roles.
- Técnicos.
- Solicitudes.
- Estados de solicitudes.
- Categorías.
- Tipos de servicio.

---

# Base de datos

Durante el desarrollo se utiliza SQLite.

La base de datos se encuentra en:

```text
db.sqlite3
```

Configuración utilizada:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

SQLite se utiliza actualmente por simplicidad durante la etapa de desarrollo.

Para producción se recomienda utilizar una base de datos preparada para entornos de despliegue, como PostgreSQL.

---

# Archivos multimedia

Los archivos subidos por los usuarios se almacenan en:

```text
media/
```

Actualmente se utilizan:

```text
media/profile_photos/
media/technician_documents/
```

Configuración:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

# Frontend

El frontend utiliza Django Templates y Tailwind CSS mediante CDN.

La plantilla principal es:

```text
templates/base.html
```

Se utilizan componentes parciales reutilizables:

```text
templates/partials/navbar.html
templates/partials/footer.html
```

---

# Diseño responsive

La interfaz está desarrollada con enfoque **mobile-first**.

La aplicación se adapta a:

- Teléfonos.
- Tablets.
- Computadoras.

Se utilizan clases responsive de Tailwind CSS para ajustar:

- Navegación.
- Formularios.
- Tarjetas.
- Paneles.
- Espaciado.
- Tipografía.
- Distribución del contenido.

La navegación principal incorpora un menú adaptable para dispositivos móviles.

---

# Tailwind CSS

Tailwind CSS se carga actualmente mediante CDN desde `base.html`.

Por este motivo, Tailwind CSS **no forma parte de `requirements.txt`**.

No es necesario instalar Tailwind mediante Python para ejecutar la versión actual del proyecto.

---

# Comandos principales de Django

## Crear migraciones

Después de modificar modelos:

```powershell
python manage.py makemigrations
```

---

## Aplicar migraciones

```powershell
python manage.py migrate
```

---

## Crear administrador

```powershell
python manage.py createsuperuser
```

---

## Comprobar configuración

```powershell
python manage.py check
```

---

## Ejecutar servidor

```powershell
python manage.py runserver
```

Para permitir conexiones desde otros dispositivos de la red local:

```powershell
python manage.py runserver 0.0.0.0:8000
```

---

# Acceso desde otro dispositivo en la misma red

Si el computador y el teléfono están conectados a la misma red Wi-Fi, Django puede ejecutarse con:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Luego se puede acceder desde el teléfono utilizando la dirección IP local del computador:

```text
http://192.168.X.X:8000/
```

La dirección IP exacta depende de la red local.

---

# Demostración mediante Cloudflare Tunnel

Para realizar pruebas desde fuera de la red local se puede utilizar Cloudflare Quick Tunnel.

Primero ejecutar Django:

```powershell
python manage.py runserver 0.0.0.0:8000
```

En otra terminal ejecutar:

```powershell
.\cloudflared.exe tunnel --url http://localhost:8000
```

Cloudflare generará una dirección temporal similar a:

```text
https://xxxxxxxx.trycloudflare.com
```

Para utilizar el túnel durante el desarrollo, `settings.py` debe permitir el dominio correspondiente.

Ejemplo:

```python
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".trycloudflare.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://xxxxxxxx.trycloudflare.com",
]
```

El dominio utilizado en `CSRF_TRUSTED_ORIGINS` debe corresponder al dominio HTTPS proporcionado por el túnel.

El Quick Tunnel está destinado a pruebas y demostraciones temporales.

No debe considerarse un despliegue de producción.

---

# Configuración de desarrollo

Actualmente el proyecto utiliza una configuración orientada al desarrollo.

Ejemplo:

```python
DEBUG = True
```

Antes de desplegar el proyecto en producción se deben modificar las configuraciones de seguridad correspondientes.

---

# Seguridad antes de producción

Antes de publicar ServiGo!! como aplicación de producción se recomienda:

- Cambiar `DEBUG` a `False`.
- Utilizar una `SECRET_KEY` segura.
- Utilizar variables de entorno.
- Configurar `ALLOWED_HOSTS` con los dominios reales.
- Configurar `CSRF_TRUSTED_ORIGINS` con los dominios reales.
- Utilizar HTTPS.
- Configurar correctamente archivos estáticos.
- Configurar correctamente archivos multimedia.
- Utilizar una base de datos de producción.
- Realizar copias de seguridad.
- Revisar permisos de usuarios.
- Revisar validación de archivos.
- Configurar el servidor de producción.

---

# Próximas etapas

La arquitectura actual permite agregar nuevas funcionalidades como módulos independientes.

Entre las funcionalidades previstas para futuras etapas se encuentran:

- Solicitudes de servicios.
- Cotizaciones.
- Agenda.
- Chat.
- Notificaciones.
- Calificaciones.
- Historial de servicios.
- Gestión de disponibilidad.
- Pagos.
- Seguimiento de servicios.
- Otras funcionalidades relacionadas con la operación de ServiGo!!.

Estas funcionalidades no forman parte de la versión actual.

---

# Estado actual

La versión actual de AppServiGo!! cuenta con la estructura base para:

- Registro.
- Autenticación.
- Usuarios.
- Roles.
- Perfil de usuario.
- Foto de perfil.
- Cambio de contraseña.
- Solicitud de técnicos.
- Perfil profesional.
- Documentación.
- Aprobación administrativa.
- Rechazo y corrección de solicitudes.
- Catálogo.
- Panel administrativo.
- Persistencia con SQLite.
- Archivos multimedia.
- Diseño responsive.
- Navegación adaptable a dispositivos móviles.

La aplicación continúa en desarrollo y la arquitectura está preparada para incorporar las siguientes etapas sin mezclar las nuevas funcionalidades con la lógica existente.

---

# Propiedad

**ServiGo!!**

Plataforma de servicios profesionales.

© 2026 ServiGo!!. Todos los derechos reservados.