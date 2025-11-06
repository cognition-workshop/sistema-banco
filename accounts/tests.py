from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.validators import validate_cpf, normalize_digits
from accounts.models import AuditLog
from django.core.exceptions import ValidationError

User = get_user_model()


class CPFValidatorTests(TestCase):
    def test_normalize_digits(self):
        self.assertEqual(normalize_digits("123.456.789-00"), "12345678900")
        self.assertEqual(normalize_digits("123 456 789 00"), "12345678900")
        self.assertEqual(normalize_digits("12345678900"), "12345678900")

    def test_valid_cpf(self):
        validate_cpf("52998224725")
        validate_cpf("529.982.247-25")

    def test_invalid_cpf_length(self):
        with self.assertRaises(ValidationError):
            validate_cpf("123")

    def test_invalid_cpf_all_same_digit(self):
        with self.assertRaises(ValidationError):
            validate_cpf("11111111111")

    def test_invalid_cpf_check_digit(self):
        with self.assertRaises(ValidationError):
            validate_cpf("12345678900")


class AdminUserManagementAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
            cpf="52998224725"
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            is_staff=False,
            cpf="15350946056"
        )

    def test_anonymous_user_redirected(self):
        response = self.client.get(reverse("admin_users:user_list"))
        self.assertEqual(response.status_code, 302)

    def test_regular_user_denied(self):
        self.client.login(username="user@example.com", password="testpass123")
        response = self.client.get(reverse("admin_users:user_list"))
        self.assertIn(response.status_code, [302, 403])

    def test_staff_user_allowed(self):
        self.client.login(username="admin@example.com", password="testpass123")
        response = self.client.get(reverse("admin_users:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gerenciar Usuários")


class AdminUserSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
            cpf="52998224725"
        )
        self.user1 = User.objects.create_user(
            email="jane@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            cpf="15350946056",
            is_active=True
        )
        self.user2 = User.objects.create_user(
            email="john@example.com",
            password="testpass123",
            first_name="John",
            last_name="Smith",
            cpf="11144477735",
            is_active=False
        )
        self.client.login(username="admin@example.com", password="testpass123")

    def test_search_by_name(self):
        response = self.client.get(reverse("admin_users:user_list"), {"q": "Jane"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jane@example.com")
        self.assertNotContains(response, "john@example.com")

    def test_search_by_email(self):
        response = self.client.get(reverse("admin_users:user_list"), {"q": "john@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "john@example.com")

    def test_search_by_cpf(self):
        response = self.client.get(reverse("admin_users:user_list"), {"cpf": "153.509.460-56"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jane@example.com")

    def test_filter_by_status_active(self):
        response = self.client.get(reverse("admin_users:user_list"), {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jane@example.com")
        self.assertNotContains(response, "john@example.com")

    def test_filter_by_status_suspended(self):
        response = self.client.get(reverse("admin_users:user_list"), {"status": "suspended"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "john@example.com")
        self.assertNotContains(response, "jane@example.com")


class AdminUserEditTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
            cpf="52998224725"
        )
        self.user1 = User.objects.create_user(
            email="jane@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            cpf="15350946056",
            phone="11999999999"
        )
        self.client.login(username="admin@example.com", password="testpass123")

    def test_edit_user_updates_fields(self):
        url = reverse("admin_users:user_edit", args=[self.user1.pk])
        response = self.client.post(url, {
            "first_name": "Janet",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "11988888888",
            "is_staff": "on",
            "is_superuser": "",
            "groups": [],
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "Janet")
        self.assertEqual(self.user1.phone, "11988888888")
        self.assertTrue(self.user1.is_staff)

    def test_edit_creates_audit_log(self):
        url = reverse("admin_users:user_edit", args=[self.user1.pk])
        self.client.post(url, {
            "first_name": "Janet",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "11999999999",
            "is_staff": "",
            "is_superuser": "",
            "groups": [],
        })
        self.assertTrue(
            AuditLog.objects.filter(
                target_user=self.user1,
                action=AuditLog.ACTION_EDIT
            ).exists()
        )

    def test_cannot_edit_own_permissions(self):
        url = reverse("admin_users:user_edit", args=[self.admin.pk])
        response = self.client.post(url, {
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@example.com",
            "phone": "",
            "is_staff": "",
            "is_superuser": "",
            "groups": [],
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)


class AdminUserToggleActiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
            cpf="52998224725"
        )
        self.user1 = User.objects.create_user(
            email="jane@example.com",
            password="testpass123",
            first_name="Jane",
            cpf="15350946056",
            is_active=True
        )
        self.client.login(username="admin@example.com", password="testpass123")

    def test_suspend_active_user(self):
        url = reverse("admin_users:user_toggle_status", args=[self.user1.pk])
        response = self.client.post(url, {"reason": "Test suspension"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.is_active)

    def test_reactivate_suspended_user(self):
        self.user1.is_active = False
        self.user1.save()
        url = reverse("admin_users:user_toggle_status", args=[self.user1.pk])
        response = self.client.post(url, {"reason": "Test reactivation"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.is_active)

    def test_suspend_creates_audit_log(self):
        url = reverse("admin_users:user_toggle_status", args=[self.user1.pk])
        self.client.post(url, {"reason": "Suspicious activity"})
        self.assertTrue(
            AuditLog.objects.filter(
                target_user=self.user1,
                action=AuditLog.ACTION_SUSPEND
            ).exists()
        )

    def test_reactivate_creates_audit_log(self):
        self.user1.is_active = False
        self.user1.save()
        url = reverse("admin_users:user_toggle_status", args=[self.user1.pk])
        self.client.post(url, {"reason": "Cleared"})
        self.assertTrue(
            AuditLog.objects.filter(
                target_user=self.user1,
                action=AuditLog.ACTION_REINSTATE
            ).exists()
        )

    def test_cannot_change_own_status(self):
        url = reverse("admin_users:user_toggle_status", args=[self.admin.pk])
        response = self.client.post(url, {"reason": "Test"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
