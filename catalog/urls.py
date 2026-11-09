from django.urls import path

from .views import (
    BrandDetailView,
    BrandListView,
    CategoryDetailView,
    CategoryListView,
    ProductDetailView,
    ProductListView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path(
        "brands/<int:pk>/",
        BrandDetailView.as_view(),
        name="brand-detail",
    ),
    path("products/", ProductListView.as_view(), name="product-list"),
    path(
        "products/<int:pk>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
]
