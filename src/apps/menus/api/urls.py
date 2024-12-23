from django.conf import settings
from django.urls import include, path

from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.menus.api.views import MenuMatchingHistoryViewSet, MenuViewSet, StandardMenuViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"standard-menus", StandardMenuViewSet, basename="standard-menu")
router.register(r"items", MenuViewSet, basename="menu")
router.register(r"matching-history", MenuMatchingHistoryViewSet, basename="matching-history")

urlpatterns = [
    path("", include(router.urls)),
]
