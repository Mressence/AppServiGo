from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("technicians", "0004_technicianprofile_category"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="TechnicianAvailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weekday", models.PositiveSmallIntegerField(choices=[(0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo")], verbose_name="Día")),
                ("start_time", models.TimeField(verbose_name="Desde")),
                ("end_time", models.TimeField(verbose_name="Hasta")),
                ("active", models.BooleanField(default=True, verbose_name="Activo")),
                ("technician", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availability_slots", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Horario disponible", "verbose_name_plural": "Horarios disponibles", "ordering": ["weekday", "start_time"]},
        ),
        migrations.AddConstraint(
            model_name="technicianavailability",
            constraint=models.CheckConstraint(condition=models.Q(start_time__lt=models.F("end_time")), name="tech_availability_valid_range"),
        ),
        migrations.AddConstraint(
            model_name="technicianavailability",
            constraint=models.UniqueConstraint(fields=("technician", "weekday", "start_time", "end_time"), name="unique_tech_weekly_slot"),
        ),
        migrations.CreateModel(
            name="AvailabilityException",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_at", models.DateTimeField(verbose_name="Desde")),
                ("end_at", models.DateTimeField(verbose_name="Hasta")),
                ("reason", models.CharField(blank=True, max_length=180, verbose_name="Motivo")),
                ("technician", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availability_exceptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Bloqueo de disponibilidad", "verbose_name_plural": "Bloqueos de disponibilidad", "ordering": ["start_at"]},
        ),
        migrations.AddConstraint(
            model_name="availabilityexception",
            constraint=models.CheckConstraint(condition=models.Q(start_at__lt=models.F("end_at")), name="tech_exception_valid_range"),
        ),
    ]
