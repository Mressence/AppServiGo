# AppServiGo!!

Proyecto Django de la **Etapa 1** de ServiGo!!

## Incluye

1. Registro y autenticación
2. Tres roles: Usuario, Técnico y Administrador
3. Perfil profesional de técnicos
4. Estado de aprobación: Pendiente, Aprobado y Rechazado
5. Catálogo de categorías y tipos de servicio
6. Panel administrativo de Django para gestionar técnicos y catálogo
7. Frontend separado del backend mediante templates, apps y rutas
8. Tailwind CSS mediante CDN

## Requisitos

- Python 3.11+ recomendado
- Django 5.2+

## Instalación

### Windows PowerShell

```powershell
cd AppServiGo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Si usas Anaconda:

```powershell
conda create -n servigo python=3.13
conda activate servigo
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## URLs principales

- `/` — Inicio
- `/accounts/registro/` — Registro
- `/accounts/login/` — Login
- `/accounts/dashboard/` — Panel según rol
- `/technicians/perfil/` — Perfil de técnico
- `/catalog/` — Catálogo
- `/admin/` — Administración Django

## Flujo de técnico

Registro como técnico → perfil creado como PENDIENTE → administrador revisa en `/admin/` → APROBADO o RECHAZADO.

## Nota de arquitectura

El proyecto está preparado para que las siguientes etapas se agreguen como módulos independientes sin mezclar la lógica de negocio con la presentación. La Etapa 1 no implementa todavía solicitudes, cotizaciones, agenda, chat, calificaciones ni otros procesos posteriores.
