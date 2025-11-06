import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestCoreViews:
    def test_home_view(self, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200
        assert 'Banking System' in str(response.content)

# Create your tests here.
