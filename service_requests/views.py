from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.models import User
from catalog.models import ServiceType
from technicians.models import TechnicianProfile
from .forms import ServiceRequestForm, QuotationForm
from .models import ServiceRequest, RequestAttachment, Quotation, validate_attachment
from .services import create_quotation, accept_quotation, transition_request


def _is_approved_technician(user):
    profile = getattr(user, "technician_profile", None)
    return user.role == User.Role.TECNICO and profile and profile.status == TechnicianProfile.Status.APROBADO


@login_required
def request_list(request):
    if request.user.is_staff or request.user.role == User.Role.ADMINISTRADOR:
        requests = ServiceRequest.objects.select_related("requester", "service_type", "assigned_technician")
    elif _is_approved_technician(request.user):
        requests = ServiceRequest.objects.filter(
            Q(requester=request.user) | Q(assigned_technician=request.user) |
            Q(status__in=[ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA])
        ).select_related("requester", "service_type", "assigned_technician").distinct()
    else:
        requests = ServiceRequest.objects.filter(requester=request.user).select_related("service_type", "assigned_technician")
    return render(request, "service_requests/list.html", {"requests": requests})


@login_required
def request_create(request):
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        files = request.FILES.getlist("attachments")
        if form.is_valid():
            try:
                for uploaded in files:
                    validate_attachment(uploaded)
            except ValidationError as exc:
                form.add_error(None, exc.message)
            else:
                service_request = form.save(commit=False)
                service_request.requester = request.user
                service_request.save()
                for uploaded in files:
                    RequestAttachment.objects.create(service_request=service_request, file=uploaded, uploaded_by=request.user)
                messages.success(request, "Tu solicitud se registró correctamente. Los técnicos aprobados podrán enviarte cotizaciones.")
                return redirect("service_requests:detail", pk=service_request.pk)
    else:
        service_id = request.GET.get("service")
        initial_service = ServiceType.objects.filter(pk=service_id, active=True, category__active=True).first() if service_id else None
        form = ServiceRequestForm(initial_service=initial_service)
    return render(request, "service_requests/create.html", {"form": form})


@login_required
def request_detail(request, pk):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("requester", "service_type", "assigned_technician").prefetch_related("attachments", "quotations__technician"), pk=pk
    )
    is_owner = service_request.requester_id == request.user.pk
    is_assigned = service_request.assigned_technician_id == request.user.pk
    is_admin = request.user.is_staff or request.user.role == User.Role.ADMINISTRADOR
    is_tech = _is_approved_technician(request.user)
    if not (is_owner or is_assigned or is_admin or (is_tech and service_request.status in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA))):
        raise PermissionDenied("No tienes permiso para ver esta solicitud.")
    if is_owner or is_admin or is_assigned:
        quotations = service_request.quotations.all()
    elif is_tech:
        quotations = service_request.quotations.filter(technician=request.user)
    else:
        quotations = []
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add_attachments":
                can_add = is_owner or is_assigned or is_admin
                if not can_add:
                    raise PermissionDenied("No tienes permiso para añadir evidencias a esta solicitud.")
                if service_request.status in (ServiceRequest.Status.COMPLETADA, ServiceRequest.Status.CANCELADA):
                    raise ValidationError("No se pueden adjuntar evidencias a una solicitud cerrada.")
                files = request.FILES.getlist("attachments")
                if not files:
                    raise ValidationError("Selecciona al menos un archivo.")
                for uploaded in files:
                    validate_attachment(uploaded)
                for uploaded in files:
                    RequestAttachment.objects.create(service_request=service_request, file=uploaded, uploaded_by=request.user)
                messages.success(request, "Las evidencias se adjuntaron correctamente.")
            elif action == "cancel":
                transition_request(request_obj=service_request, actor=request.user, target_status=ServiceRequest.Status.CANCELADA)
                messages.success(request, "La solicitud fue cancelada.")
            elif action == "accept_quote":
                quote = get_object_or_404(Quotation, pk=request.POST.get("quotation_id"), service_request=service_request)
                accept_quotation(quotation=quote, requester=request.user)
                messages.success(request, "Cotización aceptada. El técnico quedó asignado al servicio.")
            elif action == "transition":
                target = request.POST.get("target_status")
                valid_targets = {choice for choice, _label in ServiceRequest.Status.choices}
                if target not in valid_targets:
                    raise ValidationError("Estado no válido.")
                transition_request(request_obj=service_request, actor=request.user, target_status=target)
                messages.success(request, "El estado del servicio se actualizó.")
            else:
                raise ValidationError("Acción no válida.")
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))
        return redirect("service_requests:detail", pk=pk)
    return render(request, "service_requests/detail.html", {
        "service_request": service_request, "quotations": quotations,
        "is_owner": is_owner, "is_assigned": is_assigned, "is_admin": is_admin,
        "is_approved_technician": is_tech,
    })


@login_required
def quotation_create(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if not _is_approved_technician(request.user):
        raise PermissionDenied("Solo los técnicos aprobados pueden enviar cotizaciones.")
    if service_request.requester_id == request.user.pk:
        raise PermissionDenied("No puedes cotizar tu propia solicitud.")
    if service_request.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
        messages.error(request, "Esta solicitud ya no acepta cotizaciones.")
        return redirect("service_requests:detail", pk=pk)
    if request.method == "POST":
        form = QuotationForm(request.POST)
        if form.is_valid():
            try:
                quote, created = create_quotation(
                    request_obj=service_request, technician=request.user,
                    amount=form.cleaned_data["amount"], details=form.cleaned_data["details"],
                    estimated_days=form.cleaned_data["estimated_days"],
                )
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Cotización enviada." if created else "Tu cotización se actualizó.")
                return redirect("service_requests:detail", pk=pk)
    else:
        existing = service_request.quotations.filter(technician=request.user).first()
        form = QuotationForm(instance=existing)
    return render(request, "service_requests/quotation_form.html", {"form": form, "service_request": service_request})
