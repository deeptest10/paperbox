from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Brand, Category, Product


class CatalogAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Ручки")
        self.brand = Brand.objects.create(name="BIC")
        self.product = Product.objects.create(
            name="Синя ручка",
            price="25.00",
            category=self.category,
            brand=self.brand,
        )
        self.products_url = reverse("product-list")
        self.product_url = reverse("product-detail", args=[self.product.pk])

    def test_category_crud(self):
        # Створення, список, перегляд, редагування та видалення.
        url = reverse("category-list")
        response = self.client.post(url, {"name": "Зошити"}, format="json")
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        detail = reverse("category-detail", args=[pk])
        self.assertEqual(Category.objects.get(pk=pk).name, "Зошити")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(pk, [item["id"] for item in response.data])
        response = self.client.get(detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Зошити")
        response = self.client.patch(detail, {"name": "Блокноти"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.get(pk=pk).name, "Блокноти")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Category.objects.filter(pk=pk).exists())
        response = self.client.get(detail)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(set(response.data["error"]), {"message", "details"})

    def test_brand_crud(self):
        url = reverse("brand-list")
        response = self.client.post(url, {"name": "Pilot"}, format="json")
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        detail = reverse("brand-detail", args=[pk])
        self.assertEqual(Brand.objects.get(pk=pk).name, "Pilot")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(pk, [item["id"] for item in response.data])
        response = self.client.get(detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Pilot")
        response = self.client.patch(detail, {"name": "Pilot Україна"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Brand.objects.get(pk=pk).name, "Pilot Україна")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Brand.objects.filter(pk=pk).exists())
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_product_crud(self):
        data = {
            "name": "Чорна ручка",
            "price": "30.00",
            "category_id": self.category.pk,
            "brand_id": self.brand.pk,
        }
        response = self.client.post(self.products_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        detail = reverse("product-detail", args=[pk])
        self.assertEqual(Product.objects.get(pk=pk).name, "Чорна ручка")
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(pk, [item["id"] for item in response.data["results"]])
        response = self.client.get(detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "30.00")
        response = self.client.patch(detail, {"price": "0.00"}, format="json")
        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(pk=pk)
        self.assertEqual(product.price, 0)
        self.assertEqual(product.name, "Чорна ручка")
        self.assertEqual(product.category_id, self.category.pk)
        self.assertEqual(product.brand_id, self.brand.pk)
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Product.objects.filter(pk=pk).exists())
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_invalid_names(self):
        cases = [("category-list", Category, "РУЧКИ"), ("brand-list", Brand, "bic")]
        for route, model, duplicate in cases:
            for name in ["", duplicate]:
                with self.subTest(route=route, name=name):
                    response = self.client.post(
                        reverse(route), {"name": name}, format="json"
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(
                        set(response.data["error"]), {"message", "details"}
                    )
                    self.assertIn("name", response.data["error"]["details"])
                    self.assertEqual(model.objects.count(), 1)

    def test_invalid_product_data(self):
        # У тестовій базі є лише одна категорія та один бренд.
        cases = [
            ("price", "-1.00"),
            ("category_id", self.category.pk + 1),
            ("brand_id", self.brand.pk + 1),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                response = self.client.patch(
                    self.product_url, {field: value}, format="json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["error"]["details"])
                self.product.refresh_from_db()
                self.assertEqual(str(self.product.price), "25.00")
                self.assertEqual(self.product.category_id, self.category.pk)
                self.assertEqual(self.product.brand_id, self.brand.pk)

    def test_protected_deletion(self):
        for route, obj in [
            ("category-detail", self.category),
            ("brand-detail", self.brand),
        ]:
            with self.subTest(route=route):
                response = self.client.delete(reverse(route, args=[obj.pk]))
                self.assertEqual(response.status_code, 400)
                self.assertIn("detail", response.data["error"]["details"])
                obj.refresh_from_db()  # Запис має залишитися в базі.
                self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_search_filters_and_ordering(self):
        category = Category.objects.create(name="Зошити")
        brand = Brand.objects.create(name="Pilot")
        pen = Product.objects.create(
            name="Чорна ручка",
            price="40.00",
            category=self.category,
            brand=brand,
        )
        notebook = Product.objects.create(
            name="Зошит",
            price="60.00",
            category=category,
            brand=self.brand,
        )
        cases = [
            ({"search": "РУЧКА"}, [self.product.pk, pen.pk]),
            ({"search": "Неіснуючий товар"}, []),
            ({"category": self.category.pk}, [self.product.pk, pen.pk]),
            ({"brand": self.brand.pk}, [notebook.pk, self.product.pk]),
            (
                {
                    "category": self.category.pk,
                    "brand": self.brand.pk,
                    "search": "РУЧКА",
                },
                [self.product.pk],
            ),
            ({"ordering": "price"}, [self.product.pk, pen.pk, notebook.pk]),
            ({"ordering": "-price"}, [notebook.pk, pen.pk, self.product.pk]),
            ({"ordering": "name"}, [notebook.pk, self.product.pk, pen.pk]),
            ({"ordering": "-name"}, [pen.pk, self.product.pk, notebook.pk]),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                response = self.client.get(self.products_url, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], len(expected))
                self.assertEqual(
                    [item["id"] for item in response.data["results"]], expected
                )

    def test_invalid_query_parameters(self):
        cases = [
            ("page", "abc"),
            ("page", 0),
            ("category", "abc"),
            ("category", 0),
            ("brand", "abc"),
            ("brand", 0),
            ("ordering", "unknown"),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                response = self.client.get(self.products_url, {field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["error"]["details"])
        response = self.client.get(self.products_url, {"page": 999})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(set(response.data["error"]), {"message", "details"})

    def test_pagination(self):
        for number in range(20):
            Product.objects.create(
                name=f"Товар {number:02d}",
                price="10.00",
                category=self.category,
                brand=self.brand,
            )
        first = self.client.get(self.products_url, {"page": 1})
        second = self.client.get(self.products_url, {"page": 2})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["count"], 21)
        self.assertEqual(second.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNotNone(first.data["next"])
        self.assertIsNone(first.data["previous"])
        self.assertIsNone(second.data["next"])
        self.assertIsNotNone(second.data["previous"])
        ids = [item["id"] for item in first.data["results"] + second.data["results"]]
        self.assertCountEqual(ids, Product.objects.values_list("id", flat=True))
