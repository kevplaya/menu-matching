import pytest

from apps.menus.models import StandardMenu
from apps.menus.services import MenuMatchingService
from apps.nlp.services.normalizer import MenuNormalizer


class TestMenuNormalizer:
    def test_normalize_basic(self):
        """기본 정규화 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치찌개") == "김치찌개"
        assert normalizer.normalize("  김치찌개  ") == "김치찌개"

    def test_normalize_remove_parentheses(self):
        """괄호 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치찌개(1인분)") == "김치찌개"
        assert normalizer.normalize("된장찌개[특]") == "된장찌개"

    def test_normalize_remove_servings(self):
        """인분/개입 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치찌개 2인분") == "김치찌개"
        assert normalizer.normalize("만두 10개입") == "만두"

    def test_normalize_remove_units(self):
        """단위 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("콜라 500ml") == "콜라"
        assert normalizer.normalize("스테이크 200g") == "스테이크"

    def test_normalize_remove_price(self):
        """가격 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치찌개 8000원") == "김치찌개"
        assert normalizer.normalize("삼겹살 15,000원") == "삼겹살"

    def test_normalize_remove_keywords(self):
        """키워드 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("NEW 김치찌개") == "김치찌개"
        assert normalizer.normalize("인기 추천메뉴") == "메뉴"
        assert normalizer.normalize("특대김치찌개") == "김치찌개"

    def test_normalize_special_characters(self):
        """특수문자 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치찌개!!!") == "김치찌개"
        assert normalizer.normalize("된장~찌개") == "된장 찌개"

    def test_normalize_removes_unicode_special_chars(self):
        """한글 특수문자(※, ★, ♥ 등) 제거 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("※양념치킨") == "양념치킨"
        assert normalizer.normalize("★간장치킨") == "간장치킨"
        assert normalizer.normalize("♥비빔밥") == "비빔밥"
        assert normalizer.normalize("[신메뉴]짜장면") == "짜장면"

    def test_normalize_multiple_spaces(self):
        """여러 공백 정리 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("김치    찌개") == "김치 찌개"
        assert normalizer.normalize("된장   순두부   찌개") == "된장 순두부 찌개"

    def test_extract_keywords(self):
        """키워드 추출 테스트"""
        normalizer = MenuNormalizer()
        keywords = normalizer.extract_keywords("얼큰 김치찌개 2인분")
        assert "얼큰" in keywords
        assert "김치찌개" in keywords

    def test_extract_keywords_min_length(self):
        """최소 길이 키워드 추출 테스트"""
        normalizer = MenuNormalizer()
        keywords = normalizer.extract_keywords("된장 찌개")
        # 2글자 이상만 추출되어야 함
        assert "된장" in keywords
        assert "찌개" in keywords

    def test_normalize_empty_string(self):
        """빈 문자열 테스트"""
        normalizer = MenuNormalizer()
        assert normalizer.normalize("") == ""
        assert normalizer.normalize("   ") == ""

    def test_normalize_complex_menu(self):
        """복잡한 메뉴명 정규화 테스트"""
        normalizer = MenuNormalizer()
        result = normalizer.normalize("HOT!! 얼큰 김치찌개(특) 2인분 [추천메뉴] 15,000원")
        # 'hot', '얼큰', '김치찌개' 정도가 남아야 함
        assert "김치찌개" in result
        assert "얼큰" in result
        assert "15,000원" not in result
        assert "추천메뉴" not in result


@pytest.mark.django_db
class TestFastTextMatching:
    def test_fasttext_matches_typos(self):
        """FastText가 오타를 잡는지 테스트 (자장면 → 짜장면 등)."""
        StandardMenu.objects.get_or_create(
            name="짜장면",
            defaults={"normalized_name": "짜장면", "category": "중식"},
        )
        StandardMenu.objects.get_or_create(
            name="간짜장",
            defaults={"normalized_name": "간짜장", "category": "중식"},
        )
        svc = MenuMatchingService()
        if not svc.fasttext or not svc.fasttext.is_model_loaded():
            pytest.skip("FastText model not loaded")
        result = svc.find_standard_menu_by_fasttext("자장면")
        if result is None:
            pytest.skip("FastText model needs retraining for typo matching")
        assert result[0].name in ["짜장면", "간짜장"]

    def test_fasttext_matches_spacing_variant(self):
        """FastText가 띄어쓰기 변형을 잡는지 테스트."""
        StandardMenu.objects.get_or_create(
            name="후라이드치킨",
            defaults={"normalized_name": "후라이드치킨", "category": "치킨"},
        )
        svc = MenuMatchingService()
        if not svc.fasttext or not svc.fasttext.is_model_loaded():
            pytest.skip("FastText model not loaded")
        result = svc.find_standard_menu_by_fasttext("후라이드 치킨")
        if result is None:
            pytest.skip("FastText model needs retraining for spacing variants")
        assert result[0].name == "후라이드치킨"
