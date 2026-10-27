from rest_framework import serializers

from .models import Brand, Category, Product


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        categories = Category.objects.all()

        if self.instance is not None:
            categories = categories.exclude(pk=self.instance.pk)

        for category in categories:
            if category.name.casefold() == value.casefold():
                raise serializers.ValidationError("Категорія з такою назвою вже існує.")

        return value


class BrandSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Brand
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        brands = Brand.objects.all()

        if self.instance is not None:
            brands = brands.exclude(pk=self.instance.pk)

        for brand in brands:
            if brand.name.casefold() == value.casefold():
                raise serializers.ValidationError("Бренд з такою назвою вже існує.")

        return value


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source="brand",
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "image_url",
            "price",
            "category_id",
            "brand_id",
        ]
        read_only_fields = ["id"]


class ProductQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    category = serializers.IntegerField(required=False, min_value=1)
    brand = serializers.IntegerField(required=False, min_value=1)
    ordering = serializers.ChoiceField(
        choices=["price", "-price", "name", "-name"],
        default="name",
    )
    page = serializers.IntegerField(min_value=1, default=1)
