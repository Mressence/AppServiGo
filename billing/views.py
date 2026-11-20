from html import escape
from io import BytesIO
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from service_requests.models import ServiceRequest, Quotation
from .models import Invoice


def _authorized(user, service_request):
    return (user.pk == service_request.requester_id or user.is_staff or
            getattr(user, "role", "") == "ADMINISTRADOR")


@login_required
def invoice_list(request):
    if request.user.is_staff or request.user.role == "ADMINISTRADOR":
        invoices = Invoice.objects.select_related("service_request", "issued_to")
    else:
        invoices = Invoice.objects.filter(issued_to=request.user).select_related("service_request")
    return render(request, "billing/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_download(request, request_id):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("requester", "service_type", "assigned_technician"),
        pk=request_id,
    )
    if not _authorized(request.user, service_request):
        raise PermissionDenied("No puedes descargar esta factura.")
    if service_request.status != ServiceRequest.Status.COMPLETADA:
        raise PermissionDenied("La factura estará disponible cuando el servicio esté completado.")
    quotation = service_request.quotations.filter(status=Quotation.Status.ACEPTADA).select_related("technician").first()
    if not quotation:
        raise PermissionDenied("No existe una cotización aceptada para facturar.")

    # Se registra el folio al primer clic, pero jamás se guarda el PDF en disco o en MEDIA.
    invoice, _ = Invoice.objects.get_or_create(
        service_request=service_request,
        defaults={"issued_to": service_request.requester, "amount": quotation.amount,
                  "description": service_request.service_type.name},
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=48, leftMargin=48, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BrandServiGo", parent=styles["Title"], textColor=colors.HexColor("#176b50"), fontSize=22, leading=26))
    logo_path = Path(__file__).resolve().parent.parent / "static" / "images" / "servigo-logo.png"
    logo = Image(str(logo_path), width=2.6 * inch, height=0.8 * inch) if logo_path.exists() else Paragraph("ServiGo!!", styles["BrandServiGo"])
    p = lambda value: Paragraph(escape(str(value or "—")), styles["Normal"])
    story = [
        logo, Paragraph("FACTURA DE SERVICIO · DOCUMENTO DE PRUEBA", styles["Heading2"]), Spacer(1, 8),
        p("RUC: 155-000-000000-0000 (FICTICIO)"),
        p(f"Factura: {invoice.invoice_number}"),
        p(f"Fecha de emisión: {timezone.localtime(invoice.issued_at):%d/%m/%Y %H:%M}"),
        Spacer(1, 14), Paragraph("Datos del cliente", styles["Heading3"]),
        p(service_request.requester.get_full_name() or service_request.requester.username),
        p(service_request.requester.email), p(service_request.address), Spacer(1, 12),
        Paragraph("Detalle del servicio", styles["Heading3"]), p(service_request.service_type.name),
        p(f"Técnico: {quotation.technician.get_full_name() or quotation.technician.username}"),
        p(service_request.description), Spacer(1, 14),
    ]
    table = Table([
        ["Concepto", "Importe (B/.)"],
        [escape(invoice.description), f"{invoice.amount:.2f}"],
        ["TOTAL", f"{invoice.amount:.2f}"],
    ], colWidths=[4.7 * inch, 1.4 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176b50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#dce6de")),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#edf7f1")),
        ("PADDING", (0, 0), (-1, -1), 9),
    ]))
    story += [table, Spacer(1, 24), Paragraph(
        "Documento ficticio para pruebas de ServiGo. No constituye comprobante fiscal ni reemplaza una factura fiscal autorizada.",
        styles["Italic"],
    )]
    doc.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="factura_{invoice.invoice_number}.pdf"'
    return response


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("service_request"), pk=pk)
    if not _authorized(request.user, invoice.service_request):
        raise PermissionDenied
    return render(request, "billing/invoice_detail.html", {"invoice": invoice})
