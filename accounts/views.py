from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, RedirectView, ListView, UpdateView, View

from .forms import UserRegistrationForm, UserAddressForm, UserSearchForm, UserEditForm


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


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class UserManagementListView(ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search_query = self.request.GET.get('search', '').strip()
        
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserSearchForm(initial={
            'search': self.request.GET.get('search', '')
        })
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class UserEditView(UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'accounts/user_edit.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Usuário {form.instance.email} atualizado com sucesso!'
        )
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class UserSuspendToggleView(View):
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(
            request,
            'accounts/user_suspend_confirm.html',
            {'user_to_suspend': user}
        )
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        if user == request.user:
            messages.error(request, 'Você não pode suspender a si mesmo!')
            return redirect('accounts:admin_user_list')
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'ativado' if user.is_active else 'suspenso'
        messages.success(
            request,
            f'Usuário {user.email} foi {status} com sucesso!'
        )
        return redirect('accounts:admin_user_list')
