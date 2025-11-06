from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import HttpResponseRedirect, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView, ListView, DetailView, UpdateView, View
from django.db.models import Q

from .forms import UserRegistrationForm, UserAddressForm, UserEditForm, UserBankAccountEditForm, UserAddressEditForm


User = get_user_model()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


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


class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('account', 'address')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(account__account_no__icontains=search_query)
            )
        
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'suspended':
            queryset = queryset.filter(is_suspended=True)
        elif status_filter == 'active':
            queryset = queryset.filter(is_suspended=False, is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class UserDetailView(StaffRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    template_name = 'accounts/user_update.html'
    form_class = UserEditForm
    
    def get_success_url(self):
        return reverse_lazy('accounts:user_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['bank_account_form'] = UserBankAccountEditForm(self.request.POST, instance=self.object.account if hasattr(self.object, 'account') else None)
            context['address_form'] = UserAddressEditForm(self.request.POST, instance=self.object.address if hasattr(self.object, 'address') else None)
        else:
            context['bank_account_form'] = UserBankAccountEditForm(instance=self.object.account if hasattr(self.object, 'account') else None)
            context['address_form'] = UserAddressEditForm(instance=self.object.address if hasattr(self.object, 'address') else None)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        bank_account_form = context['bank_account_form']
        address_form = context['address_form']
        
        if bank_account_form.is_valid() and address_form.is_valid():
            self.object = form.save()
            if hasattr(self.object, 'account'):
                bank_account_form.save()
            if hasattr(self.object, 'address'):
                address_form.save()
            messages.success(self.request, 'User updated successfully')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class UserSuspendView(StaffRequiredMixin, View):
    def post(self, request, pk):
        user = User.objects.get(pk=pk)
        user.is_suspended = not user.is_suspended
        user.save(update_fields=['is_suspended'])
        
        status = 'suspended' if user.is_suspended else 'activated'
        messages.success(request, f'User {user.email} has been {status}')
        
        return redirect('accounts:user_detail', pk=pk)
