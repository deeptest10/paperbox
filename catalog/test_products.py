import pytest
from django.urls import reverse

from catalog.models import Product

pytestmark = pytest.mark.django_db


def test_guest_can_read_products(api_client, product):
    response = api_client.get(reverse("product-list"))

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == product.pk

    response = api_client.get(reverse("product-detail", args=[product.pk]))

    assert response.status_code == 200
    assert response.data["name"] == product.name


def test_empty_product_list(api_client):
    response = api_client.get(reverse("product-list"))

    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


@pytest.mark.parametrize(
    ("role", "expected"),
    [("guest", 401), ("user", 403), ("admin", 201)],
)
def test_create_product_permissions(
    api_client, authenticated_client, user, admin, product_data, role, expected
):
    if role != "guest":
        api_client = authenticated_client(admin if role == "admin" else user)

    response = api_client.post(reverse("product-list"), product_data, format="json")

    assert response.status_code == expected
    assert Product.objects.count() == (1 if expected == 201 else 0)

    if expected == 201:
        saved = Product.objects.get(pk=response.data["id"])
        assert saved.name == product_data["name"]
        assert str(saved.price) == "30.00"
        assert saved.category_id == product_data["category_id"]
        assert saved.brand_id == product_data["brand_id"]


@pytest.mark.parametrize(
    ("role", "expected"),
    [("guest", 401), ("user", 403), ("admin", 200)],
)
def test_update_product_permissions(
    api_client, authenticated_client, user, admin, product, role, expected
):
    if role != "guest":
        api_client = authenticated_client(admin if role == "admin" else user)

    response = api_client.patch(
        reverse("product-detail", args=[product.pk]),
        {"price": "40.00"},
        format="json",
    )

    assert response.status_code == expected
    product.refresh_from_db()
    assert str(product.price) == ("40.00" if expected == 200 else "25.00")
    assert product.name == "Синя ручка"


@pytest.mark.parametrize(
    ("role", "expected"),
    [("guest", 401), ("user", 403), ("admin", 204)],
)
def test_delete_product_permissions(
    api_client, authenticated_client, user, admin, product, role, expected
):
    if role != "guest":
        api_client = authenticated_client(admin if role == "admin" else user)

    response = api_client.delete(reverse("product-detail", args=[product.pk]))

    assert response.status_code == expected
    assert Product.objects.filter(pk=product.pk).exists() == (expected != 204)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("price", "-1.00"),
        ("price", "abc"),
        ("category_id", 999999),
        ("brand_id", 999999),
        ("image_url", "not-a-url"),
    ],
)
def test_create_product_invalid_data(
    authenticated_client, admin, product_data, field, value
):
    client = authenticated_client(admin)
    product_data[field] = value

    response = client.post(reverse("product-list"), product_data, format="json")

    assert response.status_code == 400
    assert field in response.data["error"]["details"]
    assert Product.objects.count() == 0


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_product(authenticated_client, admin, method):
    client = authenticated_client(admin)
    url = reverse("product-detail", args=[999999])

    if method == "patch":
        response = client.patch(url, {"price": "40.00"}, format="json")
    else:
        response = getattr(client, method)(url)

    assert response.status_code == 404
    assert set(response.data["error"]) == {"message", "details"}


def test_invalid_token_cannot_create_product(api_client, product_data):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

    response = api_client.post(reverse("product-list"), product_data, format="json")

    assert response.status_code == 401
    assert Product.objects.count() == 0
