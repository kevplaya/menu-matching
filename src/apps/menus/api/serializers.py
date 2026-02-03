from rest_framework import serializers

from apps.menus.models import Menu, MenuMatchingHistory, Restaurant, StandardMenu


class RestaurantSerializer(serializers.ModelSerializer):
    menu_count = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "address",
            "phone",
            "category",
            "is_active",
            "menu_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_menu_count(self, obj):
        return obj.menus.count()


class StandardMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardMenu
        fields = [
            "id",
            "name",
            "normalized_name",
            "category",
            "description",
            "match_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "match_count", "created_at", "updated_at"]


class StandardMenuListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardMenu
        fields = ["id", "name", "normalized_name", "category", "match_count"]


class MenuSerializer(serializers.ModelSerializer):
    standard_menu_detail = StandardMenuListSerializer(source="standard_menu", read_only=True)
    restaurant_detail = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "original_name",
            "normalized_name",
            "standard_menu",
            "standard_menu_detail",
            "restaurant",
            "restaurant_detail",
            "price",
            "description",
            "match_confidence",
            "match_method",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "normalized_name",
            "match_confidence",
            "match_method",
            "created_at",
            "updated_at",
        ]

    def get_restaurant_detail(self, obj):
        return {"id": obj.restaurant.id, "name": obj.restaurant.name}


class MenuCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["original_name", "restaurant", "price", "description"]


class MenuMatchRequestSerializer(serializers.Serializer):
    original_name = serializers.CharField(max_length=300, required=True)
    restaurant = serializers.IntegerField(required=True)
    price = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)


class MenuMatchingHistorySerializer(serializers.ModelSerializer):
    menu_name = serializers.CharField(source="menu.original_name", read_only=True)
    standard_menu_name = serializers.CharField(source="standard_menu.name", read_only=True)

    class Meta:
        model = MenuMatchingHistory
        fields = [
            "id",
            "menu",
            "menu_name",
            "standard_menu",
            "standard_menu_name",
            "confidence_score",
            "match_method",
            "matched_tokens",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MenuMatchResponseSerializer(serializers.Serializer):
    menu = MenuSerializer()
    matched = serializers.BooleanField()
    standard_menu = StandardMenuListSerializer(allow_null=True)
    confidence = serializers.FloatField(allow_null=True)
    method = serializers.CharField(allow_null=True)


class MenuBatchMatchRequestSerializer(serializers.Serializer):
    menus = serializers.ListField(child=MenuMatchRequestSerializer(), min_length=1, max_length=100)


class RematchResultSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    matched = serializers.IntegerField()
    success_rate = serializers.FloatField()
