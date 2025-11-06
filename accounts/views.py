from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .forms import UserRegistrationForm, UserAddressForm
from .models import AuthenticationLog


User = get_user_model()


def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_authentication_event(request, email, event_type, success=True, failure_reason='', user=None):
    """Log authentication events for audit trail"""
    AuthenticationLog.objects.create(
        user=user,
        email=email,
        event_type=event_type,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        success=success,
        failure_reason=failure_reason
    )


def rate_limit_login(max_attempts=5, window=300):
    """
    Rate limit login attempts per IP address
    max_attempts: maximum number of attempts allowed
    window: time window in seconds (default 5 minutes)
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.method == 'POST':
                ip_address = get_client_ip(request)
                cache_key = f'login_attempts_{ip_address}'
                attempts = cache.get(cache_key, 0)
                
                if attempts >= max_attempts:
                    remaining_time = cache.ttl(cache_key)
                    messages.error(
                        request,
                        f'Too many login attempts. Please try again in {remaining_time // 60} minutes.'
                    )
                    return HttpResponse('Too many login attempts', status=429)
                
                cache.set(cache_key, attempts + 1, window)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


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
            log_authentication_event(
                self.request,
                user.email,
                'login_success',
                user=user
            )
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
    
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return rate_limit_login()(view)
    
    def form_valid(self, form):
        """Log successful login and clear rate limit"""
        ip_address = get_client_ip(self.request)
        cache_key = f'login_attempts_{ip_address}'
        cache.delete(cache_key)
        
        log_authentication_event(
            self.request,
            form.get_user().email,
            'login_success',
            user=form.get_user()
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Log failed login attempt"""
        email = self.request.POST.get('username', '')
        log_authentication_event(
            self.request,
            email,
            'login_failed',
            success=False,
            failure_reason='Invalid credentials'
        )
        return super().form_invalid(form)


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            log_authentication_event(
                self.request,
                self.request.user.email,
                'logout',
                user=self.request.user
            )
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)
