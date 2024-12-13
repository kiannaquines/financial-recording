from typing import Any
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView
from app.forms import *
from app.models import *
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from io import BytesIO
from django.core.exceptions import ObjectDoesNotExist

from app.sms import send_sms_api_interface


class IndexPageView(View):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class RegisterView(View):
    template_name = "register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")

        context = {"form": RegistrationForm()}
        return render(request, self.template_name, context)

    def post(self, request):
        form = RegistrationForm(request.POST)

        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request, "You have successfully registered.", extra_tags="success"
                )
                return redirect("login")

            except Exception as e:
                messages.error(request, "An error occurred during registration.")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        context = {"form": form}

        return render(request, self.template_name, context)


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        try:
            check_user = User.objects.get(username=username)
            if not check_user.is_active:
                messages.error(
                    request,
                    "Your account is still inactive. Please contact your administrator.",
                    extra_tags="danger",
                )
        except ObjectDoesNotExist:
            pass

        messages.error(
            request,
            "Invalid username or password. Please try again.",
            extra_tags="danger",
        )
        return render(request, self.template_name, {"form": LoginForm()})


class DashboardView(View):
    template_name = "dashboard.html"

    def get(self, request):
        context = {}
        query_assistance = Assistance.objects.all()[:10]
        query_assistance_count = Assistance.objects.count()
        query_assistance_claimed_count = Assistance.objects.filter(
            is_claimed=True
        ).count()
        query_beneficiary_count = Beneficiary.objects.count()
        query_client_count = Client.objects.count()

        assistance_data = (
            Assistance.objects.annotate(month=ExtractMonth("date_added"))
            .values("month", "assistance_type")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        chart_data = {"Education": [0] * 12, "Medical": [0] * 12, "Burial": [0] * 12}

        for entry in assistance_data:
            month_index = entry["month"] - 1
            assistance_type = entry["assistance_type"]
            count = entry["count"]

            if assistance_type in chart_data:
                chart_data[assistance_type][month_index] = count

        context["chart_data"] = chart_data
        context["months"] = months

        context["assistance"] = query_assistance
        context["assistance_count"] = query_assistance_count
        context["query_assistance_claimed_count"] = query_assistance_claimed_count
        context["beneficiary_count"] = query_beneficiary_count
        context["client_count"] = query_client_count

        context["senior_count"] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[0][0]
        ).count()
        context["sole_parent_count"] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[1][0]
        ).count()
        context["pwd_count"] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[2][0]
        ).count()
        return render(request, self.template_name, context)


class UsersView(View):
    template_name = "view_templates/users.html"

    def get(self, request):
        context = {}
        query_users = User.objects.all()
        context["users"] = query_users
        return render(request, self.template_name, context)


class GenerateReportView(View):

    template_name = "report.html"

    def get(self, request):
        context = {}
        query_barangay = Client.objects.values("barangay").distinct()
        query_assistance = Assistance.objects.all().order_by("-date_added")
        context["assistance"] = query_assistance
        context["barangay"] = query_barangay
        return render(request, self.template_name, context)

    def post(self, request):
        if request.method == "POST":
            start_date = request.POST.get("from", "")
            end_date = request.POST.get("to", "")
            client_type = request.POST.get("type", "")
            assistance_type = request.POST.get("assistance_type", "")
            barangay = request.POST.get("barangay", "")

            from django.utils import timezone

            start_date = (
                datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            )
            end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

            start_date = (
                timezone.make_aware(start_date)
                if start_date and timezone.is_naive(start_date)
                else start_date
            )
            end_date = (
                timezone.make_aware(end_date)
                if end_date and timezone.is_naive(end_date)
                else end_date
            )

            query_assistance = Assistance.objects.filter(
                date_added__range=[start_date, end_date],
            )

            if not query_assistance.exists():
                messages.error(
                    request,
                    "No assistance information available in the given date range, please select a different date range.",
                    extra_tags="danger",
                )
                return HttpResponseRedirect(reverse_lazy("report"))

            if barangay:
                header_barangay = barangay
                query_assistance = query_assistance.filter(
                    client__barangay__icontains=barangay
                )
            else:
                header_barangay = "All Barangay in Carmen North Cotabato"
                query_assistance = query_assistance.all()

            if client_type:
                query_assistance = query_assistance.filter(
                    client__client_type=client_type
                )
            else:
                query_assistance = query_assistance.all()

            if assistance_type:
                header_assistance_type = assistance_type
                query_assistance = query_assistance.filter(
                    assistance_type=assistance_type
                )
            else:
                header_assistance_type = "All Assistance Type"
                query_assistance = query_assistance.all()

            buffer = BytesIO()
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="assistance_report.pdf"'

            left_margin = 1 * inch
            right_margin = 1 * inch
            top_margin = 0
            bottom_margin = 1 * inch

            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=left_margin,
                rightMargin=right_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin,
            )
            doc.title = "Carmen MSWD Transaction Report"

            elements = []

            styles = getSampleStyleSheet()
            header_style = styles["Heading2"]
            header_style.alignment = 1

            current_date = datetime.now().strftime("%Y-%m-%d")
            header = Paragraph(
                f"Carmen MSWD Transaction Report<br/>{header_barangay}<br/>{header_assistance_type}<br/><small>{current_date}</small>",
                header_style,
            )
            elements.append(header)
            elements.append(Spacer(1, 0.2 * inch))
            data = [
                [
                    "Client",
                    "Sex",
                    "Amount",
                    "Client Type",
                    "Assistance Type",
                    "Barangay",
                    "Date Released",
                ]
            ]
            for assistance in query_assistance:
                data.append(
                    [
                        str(assistance.client.get_fullname()),
                        assistance.client.gender,
                        assistance.amount,
                        assistance.client.client_type,
                        assistance.assistance_type,
                        assistance.client.barangay,
                        (
                            assistance.date_provided.strftime("%Y-%m-%d")
                            if assistance.date_provided
                            else "N/A"
                        ),
                    ]
                )

            table = Table(data)
            style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
            table.setStyle(style)
            elements.append(table)

            elements.append(Spacer(1, 0.5 * inch))

            from reportlab.lib.enums import TA_CENTER

            signatory_style = ParagraphStyle(
                name="SignatoryStyle",
                fontName="Helvetica",
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=20,
            )

            signatories = [
                "Rahid Abedin Abas <br/>_________________________<br/><br/><b>MSWD Head</b>"
            ]

            for signatory in signatories:
                elements.append(Paragraph(signatory, signatory_style))
                elements.append(Spacer(1, 0.7 * inch))

            doc.build(elements)

            buffer.seek(0)
            response.write(buffer.read())
            return response


class AssistanceView(View):
    template_name = "view_templates/assistance.html"

    def get(self, request):
        context = {}
        query_assistance = (
            Assistance.objects.all().select_related("client").order_by("-date_added")
        )
        context["assistance"] = query_assistance
        return render(request, self.template_name, context)


class AssistanceHistoryView(View):
    template_name = "view_templates/transaction_history.html"

    def get(self, request):
        context = {}
        query_assistance = (
            Assistance.objects.all().select_related("client").order_by("-date_added")
        )
        context["assistance"] = query_assistance
        return render(request, self.template_name, context)


class BeneficiaryView(View):
    template_name = "view_templates/beneficiary.html"

    def get(self, request):
        context = {}
        query_clients = Beneficiary.objects.all().order_by("date_added")
        context["beneficiaries"] = query_clients
        return render(request, self.template_name, context)


class ClientView(View):
    template_name = "view_templates/clients.html"

    def get(self, request):
        context = {}
        query_clients = Client.objects.all().order_by("date_added")
        context["clients"] = query_clients
        return render(request, self.template_name, context)


class FamilyCompositionView(View):
    template_name = "view_templates/composition.html"

    def get(self, request, pk):
        context = {}
        beneficiaries = Beneficiary.objects.filter(client_id=pk).order_by("date_added")
        context["beneficiaries"] = beneficiaries
        return render(request, self.template_name, context)


class NoticationsView(View):
    template_name = "view_templates/notifications.html"

    def get(self, request):
        context = {}
        query_notifications = NotificationSetting.objects.all().order_by(
            "-is_primary_notification"
        )
        context["notifications"] = query_notifications
        return render(request, self.template_name, context)


class AddNotificationView(CreateView):
    model = NotificationSetting
    form_class = AddNotificationForm
    success_url = reverse_lazy("notications")
    template_name = "add_templates/notification.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully added new notification template.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)


class AddClientView(CreateView):
    model = Client
    form_class = AddClientForm
    success_url = reverse_lazy("client")
    template_name = "add_templates/client.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        cleaned_birthdate = form.cleaned_data["birth_date"]
        current_date = timezone.now().date()
        age = (
            current_date.year
            - cleaned_birthdate.year
            - (
                (current_date.month, current_date.day)
                < (cleaned_birthdate.month, cleaned_birthdate.day)
            )
        )

        if age < 18:
            messages.error(
                self.request,
                "Client must be at least 18+ years old.",
                extra_tags="danger",
            )
            return super().form_invalid(form)

        messages.error(
            self.request,
            "You have successfully added new client.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)


class AddUserView(CreateView):
    model = Client
    form_class = AddUserForm
    success_url = reverse_lazy("users")
    template_name = "add_templates/user.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request, "You have successfully added new user.", extra_tags="success"
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)


class AddBeneficiaryView(CreateView):
    model = Beneficiary
    form_class = AddBeneficiaryForm
    success_url = reverse_lazy("beneficiary")
    template_name = "add_templates/beneficiary.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully added new beneficiary.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)


class AddAssistanceView(CreateView):
    model = Assistance
    form_class = AddAssistanceForm
    success_url = reverse_lazy("assistance")
    template_name = "add_templates/assistance.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully added new assistance.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)


class UpdateAssistanceView(UpdateView):
    pk_url_kwarg = "pk"
    model = Assistance
    template_name = "update_templates/assistance.html"
    form_class = UpdateAssistanceForm
    success_url = reverse_lazy("assistance")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully updated assistance.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class UpdateNotificationView(UpdateView):
    pk_url_kwarg = "pk"
    model = NotificationSetting
    template_name = "update_templates/notification.html"
    form_class = UpdateNotificationForm
    success_url = reverse_lazy("notications")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully updated notification setting.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class UpdateBeneficiaryView(UpdateView):
    pk_url_kwarg = "pk"
    model = Beneficiary
    template_name = "update_templates/beneficiary.html"
    form_class = UpdateBeneficiaryForm
    success_url = reverse_lazy("beneficiary")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully updated beneficiary.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class UpdateClientView(UpdateView):
    pk_url_kwarg = "pk"
    model = Client
    template_name = "update_templates/clients.html"
    form_class = UpdateClientForm
    success_url = reverse_lazy("client")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully updated client information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class UpdateUserView(UpdateView):
    pk_url_kwarg = "pk"
    model = User
    template_name = "update_templates/user.html"
    form_class = UpdateUserForm
    success_url = reverse_lazy("users")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully updated user information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class RemoveClientView(DeleteView):
    pk_url_kwarg = "pk"
    model = Client
    template_name = "delete_templates/clients.html"
    success_url = reverse_lazy("client")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully remove client information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class RemoveBeneficiaryView(DeleteView):
    pk_url_kwarg = "pk"
    model = Beneficiary
    template_name = "delete_templates/beneficiary.html"
    success_url = reverse_lazy("beneficiary")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully remove beneficiary information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class RemoveAssistanceView(DeleteView):
    pk_url_kwarg = "pk"
    model = Assistance
    template_name = "delete_templates/assistance.html"
    success_url = reverse_lazy("assistance")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully remove assistance information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class RemoveNotificationView(DeleteView):
    pk_url_kwarg = "pk"
    model = NotificationSetting
    template_name = "delete_templates/notification.html"
    success_url = reverse_lazy("notications")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        check_notifications = NotificationSetting.objects.exclude(
            pk=self.object.pk
        ).count()
        print("Called Delete")
        if check_notifications == 0:
            messages.error(
                request,
                "There should be at least one primary notification. Add a new notification before removing this one.",
                extra_tags="danger",
            )
            return HttpResponseRedirect(self.success_url)

        messages.success(
            request,
            "You have successfully removed the notification settings information.",
            extra_tags="success",
        )
        return super().delete(request, *args, **kwargs)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class RemoveUserView(DeleteView):
    pk_url_kwarg = "pk"
    model = User
    template_name = "delete_templates/user.html"
    success_url = reverse_lazy("users")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(
            self.request,
            "You have successfully remove user information.",
            extra_tags="success",
        )
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"{error}",
                    extra_tags="danger",
                )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class SearchAvailable(View):
    template_name = "search.html"

    def get(self, request):
        return render(request, self.template_name)





class PWDListView(View):
    template_name = 'view_templates/pwd_list.html'
    def get(self, request):
        context = {}
        context['clients'] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[2][0]
        )
        return render(request, self.template_name, context)




class SoleParentView(View):
    template_name = 'view_templates/sole_parent.html'
    def get(self, request):
        context = {}
        context['clients'] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[1][0]
        )
        return render(request, self.template_name, context)



class SeniorCitizenView(View):
    template_name = 'view_templates/senior_citizen.html'
    def get(self, request):
        context = {}
        context['clients'] = Client.objects.filter(
            client_type=Client.CLIENT_TYPE[0][0]
        )
        return render(request, self.template_name, context)


def notify_client(request):
    if request.method == "POST":
        assistance_id = request.POST.get("assistance")

        if not assistance_id:
            return JsonResponse(
                {"status": "error", "message": "Assistance ID is required."}, status=400
            )

        try:
            query_assistance = Assistance.objects.get(id=assistance_id)

            query_notification = NotificationSetting.objects.filter(
                is_primary_notification=True
            ).first()

            if not query_notification:
                return JsonResponse(
                    {"status": "error", "message": "Notification settings not found."},
                    status=400,
                )

            message = query_notification.notification_message.format(
                name=query_assistance.client.get_fullname(),
                assistance_type=query_assistance.assistance_type,
            )
            mobile = query_assistance.client.contact_number

            sms_notification = send_sms_api_interface(message=message, mobile=mobile)

            if sms_notification.get("status") == "success":
                query_assistance.is_notified = True
                query_assistance.is_ready = True
                query_assistance.save()

            return JsonResponse(sms_notification)

        except Assistance.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Assistance record not found."},
                status=404,
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": "An error occurred.", "error": str(e)},
                status=500,
            )

    return JsonResponse(
        {"status": "error", "message": "Invalid request method."}, status=405
    )


def logout_user(request):
    logout(request)
    return redirect(reverse_lazy("login"))


def autocomplete(request):
    query = request.GET.get("query", "")
    if query:

        results = Assistance.objects.filter(
            Q(client__first_name__icontains=query)
            | Q(client__last_name__icontains=query)
            | Q(client__middle_name__icontains=query)
        ).select_related("client")

        data = {
            "results": [
                {
                    "client_name": assistance.client.get_fullname(),
                    "client_first_name": assistance.client.first_name,
                    "client_last_name": assistance.client.last_name,
                    "client_middle_name": assistance.client.middle_name,
                    "assistance_type": assistance.assistance_type,
                    "is_claimed": assistance.is_claimed,
                    "is_notified": assistance.is_notified,
                    "is_ready": assistance.is_ready,
                    "date_provided": assistance.date_provided,
                    "date_added": assistance.date_added.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for assistance in results
            ]
        }
    else:
        data = {"results": []}

    return JsonResponse(data)
