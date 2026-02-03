"""
카테고리별 메뉴 매칭 테스트.
표준 메뉴와 비슷한 이름(띄어쓰기, 수량, 괄호 등)이 올바른 표준 메뉴로 매칭되는지 검증합니다.
MeCab이 없는 CI/테스트 환경에서는 공백 제거 후 정확 일치 + mock 형태소로 동작합니다.
"""
from unittest.mock import MagicMock

import pytest

from apps.menus.models import StandardMenu
from apps.menus.services import MenuMatchingService

# create_sample_data.py와 동일한 표준 메뉴 목록
STANDARD_MENUS_BY_CATEGORY = [
    ("김치찌개", "김치찌개", "한식-찌개"),
    ("된장찌개", "된장찌개", "한식-찌개"),
    ("순두부찌개", "순두부찌개", "한식-찌개"),
    ("부대찌개", "부대찌개", "한식-찌개"),
    ("청국장", "청국장", "한식-찌개"),
    ("비빔밥", "비빔밥", "한식-밥"),
    ("돌솥비빔밥", "돌솥비빔밥", "한식-밥"),
    ("김치볶음밥", "김치볶음밥", "한식-밥"),
    ("제육덮밥", "제육덮밥", "한식-밥"),
    ("삼겹살", "삼겹살", "한식-고기"),
    ("목살", "목살", "한식-고기"),
    ("갈비", "갈비", "한식-고기"),
    ("불고기", "불고기", "한식-고기"),
    ("짜장면", "짜장면", "중식"),
    ("짬뽕", "짬뽕", "중식"),
    ("탕수육", "탕수육", "중식"),
    ("볶음밥", "볶음밥", "중식"),
    ("치킨", "치킨", "치킨"),
    ("후라이드치킨", "후라이드치킨", "치킨"),
    ("양념치킨", "양념치킨", "치킨"),
    ("간장치킨", "간장치킨", "치킨"),
    ("두마리치킨", "두마리치킨", "치킨"),
    ("반반치킨", "반반치킨", "치킨"),
    ("순살치킨", "순살치킨", "치킨"),
]

# 카테고리별 테스트 예시: (original_name, 기대하는 표준 메뉴 name 또는 허용 이름 튜플)
CATEGORY_EXAMPLES = {
    "치킨": [
        ("후라이드 두마리 치킨", ("두마리치킨", "후라이드치킨")),  # 둘 중 하나 매칭
        ("탄두리 치킨", ("치킨", "후라이드치킨", "순살치킨")),  # 치킨 포함 시 후보 중 하나
        ("후라이드 치킨", "후라이드치킨"),
    ],
    "한식-찌개": [
        ("얼큰 김치찌개 1인분", "김치찌개"),
        ("된장 찌개", "된장찌개"),
        ("순두부찌개 (특)", "순두부찌개"),
    ],
    "한식-밥": [
        ("돌솥 비빔밥", "돌솥비빔밥"),
        ("김치 볶음밥", "김치볶음밥"),
        ("제육 덮밥", "제육덮밥"),
    ],
    "한식-고기": [
        ("한돈 삼겹살 200g", "삼겹살"),
        ("목살 구이", "목살"),
        ("소 갈비 탕", "갈비"),  # 공백 있어야 토큰 분리로 '갈비' 매칭
    ],
    "중식": [
        ("간 짜장", "짜장면"),  # 짜장 포함 → 짜장면
        ("해물 짬뽕", "짬뽕"),
        ("탕수육 (소)", "탕수육"),
    ],
}


@pytest.fixture
def all_standard_menus(db):
    """create_sample_data와 동일한 표준 메뉴를 DB에 생성."""
    created = []
    for name, normalized, category in STANDARD_MENUS_BY_CATEGORY:
        obj, _ = StandardMenu.objects.get_or_create(
            name=name,
            defaults={"normalized_name": normalized, "category": category},
        )
        created.append(obj)
    return created


def _mock_get_noun_tokens(text: str, min_length: int = 2):
    """MeCab 대신 공백·길이 기준 토큰 (테스트용)."""
    return [w for w in text.split() if len(w) >= min_length]


@pytest.fixture
def matching_service(all_standard_menus):
    """매칭 서비스. MeCab 없을 때 mock 형태소(공백 분리)로 동작하도록 주입."""
    service = MenuMatchingService()
    if service.mecab is None:
        mock_mecab = MagicMock()
        mock_mecab.get_noun_tokens.side_effect = _mock_get_noun_tokens
        service.mecab = mock_mecab
    return service


@pytest.mark.django_db
class TestMenuMatchingByCategory:
    """카테고리별 메뉴 매칭: 비슷한 이름이 올바른 표준 메뉴로 매칭되는지 검증."""

    @pytest.mark.parametrize(
        "category,examples",
        list(CATEGORY_EXAMPLES.items()),
        ids=list(CATEGORY_EXAMPLES.keys()),
    )
    def test_category_matching(self, matching_service, all_standard_menus, category, examples):
        """각 카테고리별 예시 3개씩 매칭 검증."""
        for original_name, expected in examples:
            allowed = (expected,) if isinstance(expected, str) else expected
            menu = matching_service.create_and_match_menu(
                original_name=original_name,
                restaurant_code=f"TEST_{category}_{hash(original_name) % 10000}",
                price=10000,
            )
            assert (
                menu.standard_menu is not None
            ), f'"{original_name}" → 표준 메뉴 매칭 실패 (기대: {allowed})'
            assert menu.standard_menu.category == category, (
                f'"{original_name}" → 카테고리 불일치: ' f"기대 {category}, 실제 {menu.standard_menu.category}"
            )
            assert menu.standard_menu.name in allowed, (
                f'"{original_name}" → 표준 메뉴명 불일치: '
                f"기대 {allowed} 중 하나, 실제 {menu.standard_menu.name}"
            )

    def test_chicken_spaced_and_variants(self, matching_service, all_standard_menus):
        """치킨: 띄어쓰기·숫자 포함 입력이 후라이드치킨/두마리치킨 등으로 매칭."""
        examples = [
            ("후라이드 치킨", "후라이드치킨"),
            ("후라이드 치킨2", "후라이드치킨"),
            ("호식이 두마리 치킨", "두마리치킨"),
        ]
        for original_name, expected_name in examples:
            menu = matching_service.create_and_match_menu(
                original_name=original_name,
                restaurant_code=f"CHICKEN_{hash(original_name) % 10000}",
                price=15000,
            )
            assert menu.standard_menu is not None, f'"{original_name}" 매칭 실패'
            assert (
                menu.standard_menu.name == expected_name
            ), f'"{original_name}" → 기대 {expected_name}, 실제 {menu.standard_menu.name}'

    def test_han_sik_stew_spaced(self, matching_service, all_standard_menus):
        """한식-찌개: 띄어쓰기·괄호가 있어도 매칭."""
        examples = [
            ("김치 찌개", "김치찌개"),
            ("된장찌개 [추천]", "된장찌개"),
            ("부대 찌개 2인", "부대찌개"),
        ]
        for original_name, expected_name in examples:
            menu = matching_service.create_and_match_menu(
                original_name=original_name,
                restaurant_code=f"STEW_{hash(original_name) % 10000}",
                price=8000,
            )
            assert menu.standard_menu is not None, f'"{original_name}" 매칭 실패'
            assert (
                menu.standard_menu.name == expected_name
            ), f'"{original_name}" → 기대 {expected_name}, 실제 {menu.standard_menu.name}'

    def test_chinese_food_variants(self, matching_service, all_standard_menus):
        """중식: 간짜장·해물짬뽕 등 변형이 표준 메뉴로 매칭."""
        examples = [
            ("짜장면", "짜장면"),
            ("짬뽕 면", "짬뽕"),
            ("탕수육 소", "탕수육"),
        ]
        for original_name, expected_name in examples:
            menu = matching_service.create_and_match_menu(
                original_name=original_name,
                restaurant_code=f"CHINESE_{hash(original_name) % 10000}",
                price=7000,
            )
            assert menu.standard_menu is not None, f'"{original_name}" 매칭 실패'
            assert (
                menu.standard_menu.name == expected_name
            ), f'"{original_name}" → 기대 {expected_name}, 실제 {menu.standard_menu.name}'
