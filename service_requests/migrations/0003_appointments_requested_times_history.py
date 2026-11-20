from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("service_requests", "0002_technicianreview"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="servicerequest", name="requested_start_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Horario solicitado"),
        ),
        migrations.AddField(
            model_name="servicerequest", name="requested_end_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Fin del horario solicitado"),
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_at", models.DateTimeField(verbose_name="Inicio")),
                ("end_at", models.DateTimeField(verbose_name="Finalización")),
                ("status", models.CharField(choices=[("PROGRAMADA", "Programada"), ("CONFIRMADA", "Confirmada"), ("COMPLETADA", "Completada"), ("CANCELADA", "Cancelada")], default="PROGRAMADA", max_length=15)),
                ("notes", models.TextField(blank=True, verbose_name="Notas")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_appointments", to=settings.AUTH_USER_MODEL)),
                ("service_request", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="appointment", to="service_requests.servicerequest", verbose_name="Solicitud")),
                ("technician", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="technician_appointments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Cita", "verbose_name_plural": "Citas", "ordering": ["start_at"]},
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(condition=models.Q(start_at__lt=models.F("end_at")), name="appointment_valid_range"),
        ),
        migrations.CreateModel(
            name="Cancellation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField(verbose_name="Motivo")),
                ("previous_status", models.CharField(blank=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cancellations", to="service_requests.appointment")),
                ("cancelled_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_cancellations", to=settings.AUTH_USER_MODEL)),
                ("service_request", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cancellations", to="service_requests.servicerequest")),
            ],
            options={"verbose_name": "Cancelación", "verbose_name_plural": "Cancelaciones", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ServiceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=100)),
                ("previous_value", models.TextField(blank=True)),
                ("new_value", models.TextField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_history_actions", to=settings.AUTH_USER_MODEL)),
                ("service_request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="service_requests.servicerequest")),
            ],
            options={"verbose_name": "Movimiento de historial", "verbose_name_plural": "Historial de servicios", "ordering": ["-created_at"]},
        ),
    ]
