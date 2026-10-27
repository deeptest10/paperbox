from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Brand, Category, Product
from .pagination import ProductPagination
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductQuerySerializer,
    ProductSerializer,
)


class CategoryListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def patch(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        try:
            category.delete()
        except ProtectedError:
            raise ValidationError(
                {
                    "detail": (
                        "Неможливо видалити категорію, оскільки вона містить "
                        "товари. Спочатку видаліть їх або змініть їхню категорію."
                    )
                }
            ) from None

        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BrandDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk)
        serializer = BrandSerializer(brand)
        return Response(serializer.data)

    def patch(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk)
        serializer = BrandSerializer(
            brand,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk)

        try:
            brand.delete()
        except ProtectedError:
            raise ValidationError(
                {
                    "detail": (
                        "Неможливо видалити бренд, оскільки він має товари. "
                        "Спочатку видаліть їх або змініть їхній бренд."
                    )
                }
            ) from None

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        query_serializer = ProductQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        products = Product.objects.all()

        if "category" in params:
            products = products.filter(category_id=params["category"])

        if "brand" in params:
            products = products.filter(brand_id=params["brand"])

        search = params.get("search", "").casefold()

        if search:
            matching_ids = []

            for product_id, name in products.values_list("id", "name"):
                if search in name.casefold():
                    matching_ids.append(product_id)

            products = products.filter(id__in=matching_ids)

        products = products.order_by(params["ordering"], "id")

        paginator = ProductPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
