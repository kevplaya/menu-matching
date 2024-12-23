import pytest

from apps.menus.models import Menu, MenuMatchingHistory, StandardMenu


@pytest.mark.django_db
class TestStandardMenu:
    def test_create_standard_menu(self):
        menu = StandardMenu.objects.create(name="김치찌개", normalized_name="김치찌개", category="한식")
        assert menu.name == "김치찌개"
        assert menu.match_count == 0
        assert menu.is_active is True

    def test_increment_match_count(self):
        menu = StandardMenu.objects.create(name="된장찌개", normalized_name="된장찌개")
        initial_count = menu.match_count
        menu.increment_match_count()
        assert menu.match_count == initial_count + 1

    def test_standard_menu_unique_name(self):
        StandardMenu.objects.create(name="비빔밥", normalized_name="비빔밥")
        with pytest.raises(Exception):
            StandardMenu.objects.create(name="비빔밥", normalized_name="비빔밥")

    def test_standard_menu_ordering(self):
        menu1 = StandardMenu.objects.create(name="메뉴1", normalized_name="메뉴1", match_count=10)
        menu2 = StandardMenu.objects.create(name="메뉴2", normalized_name="메뉴2", match_count=5)
        menu3 = StandardMenu.objects.create(name="메뉴3", normalized_name="메뉴3", match_count=15)

        menus = list(StandardMenu.objects.all())
        assert menus[0] == menu3  # 15
        assert menus[1] == menu1  # 10
        assert menus[2] == menu2  # 5


@pytest.mark.django_db
class TestMenu:
    def test_create_menu(self):
        menu = Menu.objects.create(
            original_name="김치찌개 1인분",
            normalized_name="김치찌개",
            restaurant_id="REST001",
            price=8000,
        )
        assert menu.original_name == "김치찌개 1인분"
        assert menu.restaurant_id == "REST001"
        assert menu.is_verified is False

    def test_menu_with_standard_menu(self):
        standard_menu = StandardMenu.objects.create(name="김치찌개", normalized_name="김치찌개")
        menu = Menu.objects.create(
            original_name="얼큰 김치찌개",
            normalized_name="김치찌개",
            restaurant_id="REST002",
            standard_menu=standard_menu,
            match_method="mecab",
            match_confidence=0.95,
        )
        assert menu.standard_menu == standard_menu
        assert menu.match_confidence == 0.95

    def test_menu_unique_together(self):
        Menu.objects.create(
            original_name="김치찌개",
            normalized_name="김치찌개",
            restaurant_id="REST001",
        )
        with pytest.raises(Exception):
            Menu.objects.create(
                original_name="김치찌개",
                normalized_name="김치찌개",
                restaurant_id="REST001",
            )

    def test_menu_match_methods(self):
        match_methods = ["exact", "mecab", "fasttext", "manual"]
        for method in match_methods:
            menu = Menu.objects.create(
                original_name=f"메뉴_{method}",
                normalized_name="메뉴",
                restaurant_id=f"REST_{method}",
                match_method=method,
            )
            assert menu.match_method == method


@pytest.mark.django_db
class TestMenuMatchingHistory:
    def test_create_matching_history(self):
        standard_menu = StandardMenu.objects.create(name="김치찌개", normalized_name="김치찌개")
        menu = Menu.objects.create(
            original_name="얼큰 김치찌개",
            normalized_name="김치찌개",
            restaurant_id="REST001",
        )
        history = MenuMatchingHistory.objects.create(
            menu=menu,
            standard_menu=standard_menu,
            confidence_score=0.85,
            match_method="fasttext",
            matched_tokens=["김치", "찌개"],
        )
        assert history.confidence_score == 0.85
        assert history.matched_tokens == ["김치", "찌개"]

    def test_matching_history_relationships(self):
        standard_menu = StandardMenu.objects.create(name="된장찌개", normalized_name="된장찌개")
        menu = Menu.objects.create(
            original_name="구수한 된장찌개",
            normalized_name="된장찌개",
            restaurant_id="REST002",
        )
        MenuMatchingHistory.objects.create(
            menu=menu,
            standard_menu=standard_menu,
            confidence_score=0.9,
            match_method="mecab",
        )

        assert menu.matching_histories.count() == 1

        assert standard_menu.matching_histories.count() == 1
