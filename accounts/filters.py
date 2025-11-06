import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='Email'
    )
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Active'
    )
    is_staff = django_filters.BooleanFilter(
        field_name='is_staff',
        label='Staff'
    )
    search = django_filters.CharFilter(
        method='search_filter',
        label='Search (email or name)'
    )
    
    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value) | 
            Q(first_name__icontains=value) | 
            Q(last_name__icontains=value)
        )
    
    class Meta:
        model = User
        fields = ['email', 'is_active', 'is_staff', 'search']
