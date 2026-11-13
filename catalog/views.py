import logging

from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrReadOnly

from .models import Brand, Category, Product
from .pagination import ProductPagination
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ErrorResponseSerializer,
    ProductListResponseSerializer,
    ProductQuerySerializer,
    ProductSerializer,
)

logger = logging.getLogger(__name__)
ERROR_RESPONSES = {
    400: OpenApiResponse(
        response=ErrorResponseSerializer,
        description="Некоректні дані або параметри запиту.",
        examples=[
            OpenApiExample(
                "Некоректна ціна",
                value={
                    "error": {
                        "message": "Некоректний запит.",
                        "details": {
                            "price": [
                                "Ensure this value is greater than or equal to 0.00."
                            ]
                        },
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    ),
    401: OpenApiResponse(
        response=ErrorResponseSerializer,
        description="Відсутній, недійсний або прострочений JWT-токен.",
    ),
    403: OpenApiResponse(
        response=ErrorResponseSerializer,
        description="Змінювати каталог може лише адміністратор.",
    ),
    404: OpenApiResponse(
        response=ErrorResponseSerializer,
        description="Товар або сторінку не знайдено.",
    ),
}


class CategoryListView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer

    @extend_schema(
        operation_id="categories_list",
        summary="Список категорій",
        responses=CategorySerializer(many=True),
    )
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
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer

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
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = BrandSerializer

    @extend_schema(
        operation_id="brands_list",
        summary="Список брендів",
        responses=BrandSerializer(many=True),
    )
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
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = BrandSerializer

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
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="products_list",
        summary="Список товарів",
        description=(
            "Публічний перегляд каталогу. "
            "Пошук за назвою без урахування регістру, "
            "фільтрація за категорією та брендом. "
            "Сортування за назвою або ціною. "
            "На сторінці до 20 товарів."
        ),
        parameters=[ProductQuerySerializer],
        responses={
            200: ProductListResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Некоректні параметри пошуку, фільтрації або пагінації.",
            ),
            401: ERROR_RESPONSES[401],
            404: ERROR_RESPONSES[404],
        },
    )
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

    @extend_schema(
        operation_id="products_create",
        summary="Створити товар",
        description="Потрібен JWT access-токен адміністратора (is_staff=True).",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: ERROR_RESPONSES[400],
            401: ERROR_RESPONSES[401],
            403: ERROR_RESPONSES[403],
        },
        examples=[
            OpenApiExample(
                "Новий товар",
                value={
                    "name": "Синя ручка",
                    "description": "Кулькова ручка із синім чорнилом.",
                    "price": "30.00",
                    "category_id": 1,
                    "brand_id": 1,
                },
                description="Замініть ID категорії та бренду на наявні у вашій базі.",
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        logger.info(
            "Product created: product_id=%s user_id=%s",
            product.pk,
            request.user.pk,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="products_retrieve",
        summary="Переглянути товар",
        description="Доступно без автентифікації.",
        responses={
            200: ProductSerializer,
            401: ERROR_RESPONSES[401],
            404: ERROR_RESPONSES[404],
        },
    )
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @extend_schema(
        operation_id="products_partial_update",
        summary="Редагувати товар",
        description=(
            "Потрібен JWT access-токен адміністратора (is_staff=True). "
            "Передавайте лише поля, які потрібно змінити."
        ),
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            **ERROR_RESPONSES,
        },
        examples=[
            OpenApiExample(
                "Зміна ціни",
                value={"price": "35.00"},
                request_only=True,
            ),
        ],
    )
    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Product updated: product_id=%s user_id=%s",
            product.pk,
            request.user.pk,
        )
        return Response(serializer.data)

    @extend_schema(
        operation_id="products_destroy",
        summary="Видалити товар",
        description="Потрібен JWT access-токен адміністратора (is_staff=True).",
        responses={
            204: OpenApiResponse(description="Товар видалено. Тіло відповіді порожнє."),
            401: ERROR_RESPONSES[401],
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product_id = product.pk
        product.delete()
        logger.info(
            "Product deleted: product_id=%s user_id=%s",
            product_id,
            request.user.pk,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
