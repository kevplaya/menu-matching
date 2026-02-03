from django.contrib import admin

from .models import Menu, MenuMatchingHistory, Restaurant, StandardMenu


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "phone", "is_active", "created_at"]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "address", "phone"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]


@admin.register(StandardMenu)
class StandardMenuAdmin(admin.ModelAdmin):
    list_display = ["name", "normalized_name", "category", "match_count", "is_active", "created_at"]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "normalized_name", "description"]
    readonly_fields = ["match_count", "created_at", "updated_at"]
    ordering = ["-match_count", "name"]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = [
        "original_name",
        "restaurant",
        "standard_menu",
        "match_method",
        "match_confidence",
        "is_verified",
        "created_at",
    ]
    list_filter = ["match_method", "is_verified", "created_at"]
    search_fields = ["original_name", "normalized_name", "restaurant__name"]
    readonly_fields = ["normalized_name", "created_at", "updated_at"]
    autocomplete_fields = ["standard_menu", "restaurant"]
    ordering = ["-created_at"]


@admin.register(MenuMatchingHistory)
class MenuMatchingHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "menu",
        "standard_menu",
        "confidence_score",
        "match_method",
        "created_at",
    ]
    list_filter = ["match_method", "created_at"]
    search_fields = ["menu__original_name", "standard_menu__name"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
