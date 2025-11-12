from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .forms import UserRegistrationForm, UserAddressForm


User = get_user_model()


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            login(self.request, user)
            messages.success(
                self.request,
                (
                    f'Thank You For Creating A Bank Account. '
                    f'Your Account Number is {user.account.account_no}. '
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('transactions:deposit_money')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = UserRegistrationForm()
        if 'address_form' not in kwargs:
            kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)


class UserLoginView(LoginView):
    template_name='accounts/user_login.html'
    redirect_authenticated_user = True


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, UpdateView

from .forms import UserSearchForm, AdminUserEditForm
from .models import AuditLog


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class AdminUserListView(StaffRequiredMixin, ListView):
    template_name = "accounts/user_management.html"
    model = User
    paginate_by = 20
    context_object_name = "users"

    def get_queryset(self):
        qs = super().get_queryset().all()
        form = UserSearchForm(self.request.GET or None)
        self.search_form = form
        if form.is_valid():
            qs = form.apply(qs)
        else:
            qs = qs.order_by("-date_joined")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = getattr(self, "search_form", UserSearchForm(self.request.GET or None))
        return ctx


class AdminUserEditView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserEditForm
    template_name = "accounts/user_edit.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        old = self.get_object()
        before = {
            "first_name": old.first_name,
            "last_name": old.last_name,
            "email": old.email,
            "phone": old.phone,
            "is_staff": old.is_staff,
            "is_superuser": old.is_superuser,
            "groups": list(old.groups.values_list("name", flat=True)),
        }
        resp = super().form_valid(form)
        new = self.get_object()
        after = {
            "first_name": new.first_name,
            "last_name": new.last_name,
            "email": new.email,
            "phone": new.phone,
            "is_staff": new.is_staff,
            "is_superuser": new.is_superuser,
            "groups": list(new.groups.values_list("name", flat=True)),
        }
        changes = {k: {"from": before[k], "to": after[k]} for k in after if before[k] != after[k]}
        if changes:
            AuditLog.objects.create(
                actor=self.request.user,
                target_user=new,
                action=AuditLog.ACTION_EDIT,
                changes=changes
            )
        messages.success(self.request, "Dados do usuário atualizados.")
        return resp

    def get_success_url(self):
        return reverse("admin_users:user_list")


class AdminUserToggleActiveView(StaffRequiredMixin, View):
    template_name = "accounts/user_confirm_status.html"

    def get(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        if request.user.pk == target.pk:
            messages.error(request, "Você não pode alterar seu próprio status.")
            return redirect("admin_users:user_list")
        return render(request, self.template_name, {"target": target})

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        if request.user.pk == target.pk:
            messages.error(request, "Você não pode alterar seu próprio status.")
            return redirect("admin_users:user_list")
        reason = (request.POST.get("reason") or "").strip()
        before = target.is_active
        target.is_active = not target.is_active
        target.save(update_fields=["is_active"])
        AuditLog.objects.create(
            actor=request.user,
            target_user=target,
            action=AuditLog.ACTION_REINSTATE if target.is_active else AuditLog.ACTION_SUSPEND,
            changes={"is_active": {"from": before, "to": target.is_active}},
            reason=reason,
        )
        messages.success(
            request,
            "Usuário reativado." if target.is_active else "Usuário suspenso."
        )
        return redirect("admin_users:user_list")
