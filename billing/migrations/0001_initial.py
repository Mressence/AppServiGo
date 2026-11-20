from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("service_requests", "0003_appointments_requested_times_history"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_number", models.CharField(blank=True, max_length=30, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.CharField(max_length=255)),
                ("issued_at", models.DateTimeField(auto_now_add=True)),
                ("issued_to", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to=settings.AUTH_USER_MODEL)),
                ("service_request", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="invoice", to="service_requests.servicerequest")),
            ],
            options={"verbose_name": "Factura", "verbose_name_plural": "Facturas", "ordering": ["-issued_at"]},
        ),
    ]
