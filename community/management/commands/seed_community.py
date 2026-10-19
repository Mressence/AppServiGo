
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from community.models import Category, Post


class Command(BaseCommand):
    help = "Crea categorías y publicaciones iniciales de demostración."

    def handle(self, *args, **options):
        User = get_user_model()
        author = User.objects.filter(is_superuser=True).first()

        if author is None:
            author = User.objects.filter(is_staff=True).first()

        if author is None:
            author = User.objects.filter(role="ADMINISTRADOR").first()

        if author is None:
            raise CommandError(
                "Crea primero un usuario administrador para atribuir "
                "las publicaciones iniciales."
            )

        categories_data = [
            ("Plomería", "Consejos sobre fugas, grifos y tuberías."),
            ("Electricidad", "Orientación general sobre instalaciones eléctricas."),
            ("Climatización", "Aire acondicionado y ventilación."),
            ("Mantenimiento", "Cuidados preventivos del hogar."),
            ("Remodelación", "Ideas y planificación de mejoras."),
        ]

        categories = {}
        for name, description in categories_data:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "is_active": True,
                },
            )
            categories[name] = category

        posts_data = [
            (
                "Plomería",
                "¿Qué debo hacer si descubro una fuga de agua?",
                "Como primera medida, si puedes hacerlo con seguridad, "
                "cierra la llave de paso correspondiente y evita el contacto "
                "del agua con enchufes o equipos eléctricos. Si la fuga es "
                "importante, hay riesgo eléctrico o no puedes detenerla, "
                "busca ayuda profesional. Esta guía es orientativa y no "
                "sustituye una inspección.",
            ),
            (
                "Electricidad",
                "¿Cuándo debo llamar a un electricista?",
                "Si notas olor a quemado, chispas, tomacorrientes calientes "
                "o interrupciones repetidas del suministro, no manipules "
                "el cableado. Si existe una situación peligrosa, aléjate "
                "y solicita ayuda cualificada. No intentes reparar circuitos "
                "energizados por tu cuenta.",
            ),
            (
                "Climatización",
                "¿Cómo puedo cuidar el aire acondicionado?",
                "Revisa las instrucciones del fabricante y mantén limpios "
                "los filtros siguiendo sus indicaciones. Mantén despejadas "
                "las entradas y salidas de aire. Si el equipo no enfría, "
                "presenta fugas o produce ruidos inusuales, una revisión "
                "profesional puede ayudar a identificar el problema.",
            ),
            (
                "Mantenimiento",
                "¿Por qué conviene hacer mantenimiento preventivo?",
                "Las revisiones periódicas pueden ayudar a detectar desgaste "
                "y problemas antes de que se agraven. Puedes organizar "
                "recordatorios para revisar grifos, ventilación y equipos "
                "domésticos siguiendo las recomendaciones de cada fabricante.",
            ),
            (
                "Remodelación",
                "¿Qué debería considerar antes de remodelar una habitación?",
                "Define el alcance del trabajo, fija un presupuesto con un "
                "margen para imprevistos y anota los materiales que necesitas. "
                "Antes de comenzar, confirma qué trabajos requieren personal "
                "cualificado o permisos. Solicita presupuestos detallados "
                "para comparar el mismo alcance de trabajo.",
            ),
            (
                "Plomería",
                "¿Qué información conviene compartir al solicitar una reparación?",
                "Describe el problema, indica en qué lugar ocurre y desde "
                "cuándo lo notas. Si es seguro, puedes aportar fotografías "
                "del área afectada. Evita compartir públicamente tu dirección "
                "completa, teléfonos u otros datos personales.",
            ),
        ]

        created_count = 0

        for category_name, title, body in posts_data:
            post, created = Post.objects.get_or_create(
                title=title,
                is_seed=True,
                defaults={
                    "author": author,
                    "category": categories[category_name],
                    "body": body,
                    "status": Post.Status.APPROVED,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Comunidad preparada. Nuevas publicaciones: {created_count}. "
                f"Autor de demostración: {author.username}."
            )
        )
