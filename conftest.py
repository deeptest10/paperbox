import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from catalog.models import Brand, Category, Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="test_user",
        password="Test-password-472!",
    )


@pytest.fixture
def admin(db):
    return get_user_model().objects.create_user(
        username="test_admin",
        password="Test-password-472!",
        is_staff=True,
    )


@pytest.fixture
def authenticated_client(api_client):
    def login(account):
        response = api_client.post(
            reverse("login"),
            {
                "username": account.username,
                "password": "Test-password-472!",
            },
            format="json",
        )
        assert response.status_code == 200
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return api_client

    return login


@pytest.fixture
def category(db):
    return Category.objects.create(name="Ручки")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="BIC")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        name="Синя ручка",
        description="Кулькова ручка",
        price="25.00",
        category=category,
        brand=brand,
    )


@pytest.fixture
def product_data(category, brand):
    return {
        "name": "Чорна ручка",
        "description": "Ручка для письма",
        "price": "30.00",
        "category_id": category.pk,
        "brand_id": brand.pk,
    }
