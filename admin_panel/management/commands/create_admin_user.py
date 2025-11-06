from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin_panel.models import AdminUser
from admin_panel.constants import SENIOR_ADMIN

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user for the admin panel'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Admin user email')
        parser.add_argument('--password', type=str, help='Admin user password')
        parser.add_argument('--role', type=str, default=SENIOR_ADMIN, 
                          help='Admin role (SENIOR, OPERATIONAL, VIEWER)')
        parser.add_argument('--first-name', type=str, default='Admin', 
                          help='First name')
        parser.add_argument('--last-name', type=str, default='User', 
                          help='Last name')
    
    def handle(self, *args, **options):
        email = options['email']
        password = options.get('password')
        role = options['role']
        first_name = options['first_name']
        last_name = options['last_name']
        
        if not password:
            password = User.objects.make_random_password(length=12)
            self.stdout.write(self.style.WARNING(f'Generated password: {password}'))
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(self.style.WARNING(f'User {email} already exists'))
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created user {email}'))
        
        admin_user, created = AdminUser.objects.get_or_create(
            user=user,
            defaults={'role': role, 'is_admin_active': True}
        )
        
        if not created:
            admin_user.role = role
            admin_user.is_admin_active = True
            admin_user.save()
            self.stdout.write(self.style.WARNING(f'Updated admin user {email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created admin user {email} with role {role}'))
        
        self.stdout.write(self.style.SUCCESS('Admin user setup complete!'))
