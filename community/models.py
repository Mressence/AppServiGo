
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("Nombre", max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    description = models.CharField("Descripción", max_length=200, blank=True)
    is_active = models.BooleanField("Activa", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoría de comunidad"
        verbose_name_plural = "categorías de comunidad"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "categoria"
            candidate = base_slug
            number = 2
            while Category.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{number}"
                number += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente de revisión"
        APPROVED = "APPROVED", "Publicado"
        REJECTED = "REJECTED", "Rechazado"
        HIDDEN = "HIDDEN", "Oculto"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
        verbose_name="Autor",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="Categoría",
    )
    title = models.CharField("Título", max_length=160)
    body = models.TextField("Contenido")
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    is_seed = models.BooleanField(
        "Contenido inicial de demostración",
        default=False,
        help_text="Identifica publicaciones iniciales creadas para la presentación.",
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "publicación"
        verbose_name_plural = "publicaciones"

    def __str__(self):
        return self.title


class Comment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente de revisión"
        APPROVED = "APPROVED", "Publicado"
        REJECTED = "REJECTED", "Rechazado"
        HIDDEN = "HIDDEN", "Oculto"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Publicación",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
        verbose_name="Autor",
    )
    body = models.TextField("Respuesta", max_length=3000)
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"

    def __str__(self):
        return f"Respuesta a: {self.post.title}"


class Vote(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="community_unique_post_vote",
            )
        ]
        verbose_name = "voto útil"
        verbose_name_plural = "votos útiles"

    def __str__(self):
        return f"{self.user} - {self.post}"


class Report(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        REVIEWED = "REVIEWED", "Revisado"
        DISMISSED = "DISMISSED", "Descartado"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Publicación reportada",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_reports",
        verbose_name="Usuario que reporta",
    )
    REASON_CHOICES = [
        ("spam", "Spam o publicidad no deseada"),
        ("offensive", "Contenido ofensivo"),
        ("misinformation", "Información potencialmente engañosa"),
        ("unsafe", "Consejo potencialmente peligroso"),
        ("other", "Otro motivo"),
    ]

    reason = models.CharField(
        "Motivo",
        max_length=100,
        choices=REASON_CHOICES,
    )
    details = models.TextField("Detalles adicionales", blank=True, max_length=1500)
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField("Fecha del reporte", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "reporte de comunidad"
        verbose_name_plural = "reportes de comunidad"
        constraints = [
            models.UniqueConstraint(
                fields=["post", "reporter"],
                name="community_unique_post_reporter",
            )
        ]

    def __str__(self):
        return f"Reporte: {self.post.title}"
