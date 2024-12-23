from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.menus.models import Menu, StandardMenu


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_menus():
    menus = [
        StandardMenu.objects.create(name="김치찌개", normalized_name="김치찌개", category="한식"),
        StandardMenu.objects.create(name="된장찌개", normalized_name="된장찌개", category="한식"),
        StandardMenu.objects.create(name="비빔밥", normalized_name="비빔밥", category="한식"),
    ]
    return menus


@pytest.mark.django_db
class TestStandardMenuAPI:
    def test_list_standard_menus(self, api_client, standard_menus):
        url = reverse("standard-menu-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_create_standard_menu(self, api_client):
        url = reverse("standard-menu-list")
        data = {
            "name": "삼겹살",
            "normalized_name": "삼겹살",
            "category": "한식",
            "description": "돼지고기 삼겹살",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "삼겹살"
        assert StandardMenu.objects.filter(name="삼겹살").exists()

    def test_retrieve_standard_menu(self, api_client, standard_menus):
        menu = standard_menus[0]
        url = reverse("standard-menu-detail", args=[menu.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == menu.name

    def test_update_standard_menu(self, api_client, standard_menus):
        menu = standard_menus[0]
        url = reverse("standard-menu-detail", args=[menu.id])
        data = {"category": "찌개류"}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["category"] == "찌개류"

    def test_delete_standard_menu(self, api_client, standard_menus):
        menu = standard_menus[0]
        url = reverse("standard-menu-detail", args=[menu.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not StandardMenu.objects.filter(id=menu.id).exists()

    def test_popular_standard_menus(self, api_client, standard_menus):
        standard_menus[0].match_count = 10
        standard_menus[0].save()
        standard_menus[1].match_count = 5
        standard_menus[1].save()

        url = reverse("standard-menu-popular")
        response = api_client.get(url, {"limit": 2})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["match_count"] == 10


@pytest.mark.django_db
class TestMenuAPI:
    def test_create_menu(self, api_client, standard_menus):
        url = reverse("menu-list")
        data = {
            "original_name": "김치찌개",
            "restaurant_id": "REST001",
            "price": 8000,
            "description": "얼큰한 김치찌개",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["original_name"] == "김치찌개"
        assert response.data["standard_menu"] is not None

    def test_list_menus(self, api_client, standard_menus):
        Menu.objects.create(
            original_name="김치찌개",
            normalized_name="김치찌개",
            restaurant_id="REST001",
            standard_menu=standard_menus[0],
        )

        url = reverse("menu-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_match_menu(self, api_client, standard_menus):
        url = reverse("menu-match")
        data = {
            "original_name": "김치찌개 1인분",
            "restaurant_id": "REST002",
            "price": 7000,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["matched"] is True
        assert response.data["standard_menu"] is not None

    def test_batch_match_menus(self, api_client, standard_menus):
        url = reverse("menu-batch-match")
        data = {
            "menus": [
                {"original_name": "김치찌개", "restaurant_id": "REST001", "price": 8000},
                {"original_name": "된장찌개", "restaurant_id": "REST001", "price": 7000},
            ]
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["matched"] is True
        assert response.data[1]["matched"] is True

    def test_by_restaurant(self, api_client, standard_menus):
        Menu.objects.create(
            original_name="김치찌개",
            normalized_name="김치찌개",
            restaurant_id="REST001",
        )
        Menu.objects.create(
            original_name="된장찌개",
            normalized_name="된장찌개",
            restaurant_id="REST001",
        )

        url = reverse("menu-by-restaurant")
        response = api_client.get(url, {"restaurant_id": "REST001"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_rematch_unmatched(self, api_client, standard_menus):
        Menu.objects.create(
            original_name="알 수 없는 메뉴",
            normalized_name="알 수 없는 메뉴",
            restaurant_id="REST001",
        )

        url = reverse("menu-rematch-unmatched")
        response = api_client.post(url, {"limit": 10})

        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "matched" in response.data
        assert "success_rate" in response.data
