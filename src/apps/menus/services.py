import logging
from typing import Dict, List, Optional, Tuple

from django.db.models import Q

from apps.menus.models import Menu, MenuMatchingHistory, StandardMenu
from apps.nlp.services.fasttext_matcher import FastTextMatcher
from apps.nlp.services.mecab_analyzer import MecabAnalyzer
from apps.nlp.services.normalizer import MenuNormalizer

logger = logging.getLogger(__name__)


class MenuMatchingService:
    def __init__(self):
        self.normalizer = MenuNormalizer()
        try:
            self.mecab = MecabAnalyzer()
        except (ImportError, RuntimeError) as e:
            logger.exception(
                "MeCab 초기화 실패: %s (원인 확인 후 mecab-ko-dic 설치 또는 MECAB_DIC_PATH 설정)",
                e,
            )
            self.mecab = None

        try:
            self.fasttext = FastTextMatcher()
        except ImportError:
            self.fasttext = None

    def normalize_menu_name(self, menu_name: str) -> str:
        return self.normalizer.normalize(menu_name)

    def find_standard_menu_by_exact_match(self, normalized_name: str) -> Optional[StandardMenu]:
        """
        정확히 일치하는 표준 메뉴를 찾습니다.

        Args:
            normalized_name: 정규화된 메뉴명

        Returns:
            표준 메뉴 객체 또는 None
        """
        return StandardMenu.objects.filter(normalized_name=normalized_name, is_active=True).first()

    # 카테고리별 대표 표준 메뉴 (동점·유사 시 우선 선택)
    CATEGORY_DEFAULT_NAMES = {
        "치킨": "후라이드치킨",
        "한식-찌개": "김치찌개",
        "한식-밥": "비빔밥",
        "한식-고기": "삼겹살",
        "중식": "짜장면",
    }

    def _common_nouns_with_substring(
        self,
        nouns: List[str],
        candidate_nouns: List[str],
        candidate_name: str,
        candidate_normalized: str,
        original_name: str,
    ) -> set:
        """형태소 집합 교집합 + 표준명/입력문자열에 포함된 토큰(부분 문자열)까지 포함."""
        exact = set(nouns) & set(candidate_nouns)
        # 입력 명사가 표준 메뉴명에 포함되면 매칭 (예: '후라이드','치킨' in '후라이드치킨')
        in_candidate = {n for n in nouns if n in candidate_name or n in candidate_normalized}
        # 표준 메뉴 명사가 입력 문자열에 포함되면 매칭
        in_input = {c for c in candidate_nouns if c in original_name}
        return exact | in_candidate | in_input

    def find_standard_menu_by_mecab(
        self, original_name: str, threshold: float = 0.35
    ) -> Optional[Tuple[StandardMenu, float, List[str]]]:
        """
        Mecab 형태소 분석을 통해 표준 메뉴를 찾습니다.
        형태소 교집합뿐 아니라, 표준명/입력문자열에 부분 문자열로 포함된 경우도 매칭합니다.

        Args:
            original_name: 원본 메뉴명
            threshold: 최소 매칭 임계값

        Returns:
            (표준 메뉴, 신뢰도, 매칭된 토큰) 또는 None
        """
        if not self.mecab:
            logger.debug("mecab: MeCab 없음, 스킵 original_name=%r", original_name)
            return None

        nouns = self.mecab.get_noun_tokens(original_name, min_length=2)
        if not nouns:
            # MeCab이 한글을 인식 못할 때(예: ipadic) 공백·연속 글자 기준 토큰 사용
            nouns = [w for w in original_name.split() if len(w) >= 2]
        if not nouns and len(original_name.strip()) >= 2:
            nouns = [original_name.strip()]

        if not nouns:
            logger.debug("mecab: 추출된 명사 없음 original_name=%r", original_name)
            return None

        logger.debug("mecab: 명사 추출 original_name=%r nouns=%s", original_name, nouns)

        query = Q()
        for noun in nouns:
            query |= Q(name__icontains=noun) | Q(normalized_name__icontains=noun)

        candidates = StandardMenu.objects.filter(query, is_active=True)
        if not candidates.exists():
            logger.debug("mecab: 후보 없음 original_name=%r nouns=%s", original_name, nouns)
            return None

        logger.debug("mecab: 후보 %d개 nouns=%s", candidates.count(), nouns)

        best_match = None
        best_score = threshold
        best_tokens: List[str] = []

        for candidate in candidates:
            candidate_nouns = self.mecab.get_noun_tokens(candidate.name, min_length=2)
            if not candidate_nouns and len(candidate.name) >= 2:
                candidate_nouns = [candidate.name]
            common_nouns = self._common_nouns_with_substring(
                nouns,
                candidate_nouns,
                candidate.name,
                candidate.normalized_name,
                original_name,
            )
            if not common_nouns:
                continue

            score = max(
                len(common_nouns) / len(nouns),
                len(common_nouns) / len(candidate_nouns) if candidate_nouns else 0,
            )

            def _is_category_default(c: StandardMenu) -> bool:
                default = self.CATEGORY_DEFAULT_NAMES.get(c.category)
                return default == c.name if default else False

            take = (
                best_match is None
                or score > best_score
                or (score == best_score and len(common_nouns) > len(best_tokens))
                or (
                    score == best_score
                    and len(common_nouns) == len(best_tokens)
                    and _is_category_default(candidate)
                    and not _is_category_default(best_match)
                )
            )
            if take:
                best_score = score
                best_match = candidate
                best_tokens = list(common_nouns)

        if best_match:
            logger.info(
                "mecab: 매칭 성공 original_name=%r → %s (score=%.3f, tokens=%s)",
                original_name,
                best_match.name,
                best_score,
                best_tokens,
            )
            return (best_match, best_score, best_tokens)

        logger.debug(
            "mecab: 임계값 미달 original_name=%r threshold=%.2f 후보 %d개 중 최고점 없음",
            original_name,
            threshold,
            candidates.count(),
        )
        return None

    def find_standard_menu_by_fasttext(
        self, normalized_name: str, threshold: float = 0.7
    ) -> Optional[Tuple[StandardMenu, float]]:
        """
        FastText를 사용하여 표준 메뉴를 찾습니다.

        Args:
            normalized_name: 정규화된 메뉴명
            threshold: 최소 유사도 임계값

        Returns:
            (표준 메뉴, 유사도) 또는 None
        """
        if not self.fasttext or not self.fasttext.is_model_loaded():
            logger.debug("fasttext: 모델 없음 또는 미로드 normalized_name=%r", normalized_name)
            return None

        # 활성화된 표준 메뉴 목록
        standard_menus = StandardMenu.objects.filter(is_active=True)
        if not standard_menus.exists():
            return None

        candidates = {sm.id: sm.normalized_name for sm in standard_menus}
        candidate_names = list(candidates.values())

        # FastText로 가장 유사한 메뉴 찾기
        result = self.fasttext.find_best_match(normalized_name, candidate_names, threshold)

        if result:
            best_name, similarity = result
            # ID로 표준 메뉴 찾기
            for sm_id, name in candidates.items():
                if name == best_name:
                    standard_menu = StandardMenu.objects.get(id=sm_id)
                    return (standard_menu, similarity)

        return None

    def match_menu(self, menu: Menu, save_history: bool = True) -> Optional[StandardMenu]:
        """
        메뉴에 대한 표준 메뉴를 찾아 매칭합니다.

        Args:
            menu: 매칭할 메뉴 객체
            save_history: 매칭 히스토리 저장 여부

        Returns:
            매칭된 표준 메뉴 또는 None
        """
        logger.debug(
            "match_menu: 시작 original_name=%r normalized=%r",
            menu.original_name,
            menu.normalized_name,
        )

        # 1. 정확 일치 확인
        standard_menu = self.find_standard_menu_by_exact_match(menu.normalized_name)
        if not standard_menu:
            # 띄어쓰기만 다른 경우: 공백 제거 후 정확 일치 (MeCab 없이도 동작)
            no_space = menu.normalized_name.replace(" ", "")
            if no_space != menu.normalized_name:
                standard_menu = self.find_standard_menu_by_exact_match(no_space)
                if standard_menu:
                    logger.debug("match_menu: 공백 제거 후 정확 일치 no_space=%r", no_space)
        if standard_menu:
            menu.standard_menu = standard_menu
            menu.match_method = "exact"
            menu.match_confidence = 1.0
            menu.save()

            if save_history:
                MenuMatchingHistory.objects.create(
                    menu=menu,
                    standard_menu=standard_menu,
                    confidence_score=1.0,
                    match_method="exact",
                    matched_tokens=[],
                )

            standard_menu.increment_match_count()
            logger.info(
                "match_menu: exact 매칭 original_name=%r → %s", menu.original_name, standard_menu.name
            )
            return standard_menu

        # 2. Mecab 형태소 분석
        logger.debug("match_menu: exact 실패, mecab 시도 original_name=%r", menu.original_name)
        mecab_result = self.find_standard_menu_by_mecab(menu.original_name)
        if mecab_result:
            standard_menu, confidence, tokens = mecab_result
            menu.standard_menu = standard_menu
            menu.match_method = "mecab"
            menu.match_confidence = confidence
            menu.save()

            if save_history:
                MenuMatchingHistory.objects.create(
                    menu=menu,
                    standard_menu=standard_menu,
                    confidence_score=confidence,
                    match_method="mecab",
                    matched_tokens=tokens,
                )

            standard_menu.increment_match_count()
            logger.info(
                "match_menu: mecab 매칭 original_name=%r → %s", menu.original_name, standard_menu.name
            )
            return standard_menu

        # 3. FastText 매칭
        logger.debug("match_menu: mecab 실패, fasttext 시도 normalized_name=%r", menu.normalized_name)
        fasttext_result = self.find_standard_menu_by_fasttext(menu.normalized_name)
        if fasttext_result:
            standard_menu, similarity = fasttext_result
            menu.standard_menu = standard_menu
            menu.match_method = "fasttext"
            menu.match_confidence = similarity
            menu.save()

            if save_history:
                MenuMatchingHistory.objects.create(
                    menu=menu,
                    standard_menu=standard_menu,
                    confidence_score=similarity,
                    match_method="fasttext",
                    matched_tokens=[],
                )

            standard_menu.increment_match_count()
            logger.info(
                "match_menu: fasttext 매칭 original_name=%r → %s",
                menu.original_name,
                standard_menu.name,
            )
            return standard_menu

        logger.warning(
            "match_menu: 매칭 실패 original_name=%r (exact/mecab/fasttext 모두 실패)", menu.original_name
        )
        return None

    def create_and_match_menu(
        self,
        original_name: str,
        restaurant=None,
        restaurant_code: str = "",
        price: Optional[int] = None,
        description: str = "",
    ) -> Menu:
        """
        새로운 메뉴를 생성하고 자동으로 매칭합니다.

        Args:
            original_name: 원본 메뉴명
            restaurant: Restaurant 객체
            restaurant_code: 음식점 코드 (레거시)
            price: 가격
            description: 설명

        Returns:
            생성된 메뉴 객체
        """
        # 정규화
        normalized_name = self.normalize_menu_name(original_name)

        # 메뉴 생성
        menu = Menu.objects.create(
            original_name=original_name,
            normalized_name=normalized_name,
            restaurant=restaurant,
            restaurant_code=restaurant_code,
            price=price,
            description=description,
        )

        # 매칭 시도
        self.match_menu(menu)

        return menu

    def rematch_unmatched_menus(self, limit: int = 100) -> Dict[str, int]:
        """
        매칭되지 않은 메뉴들을 다시 매칭 시도합니다.

        Args:
            limit: 처리할 최대 메뉴 개수

        Returns:
            {'total': 전체 개수, 'matched': 매칭 성공 개수}
        """
        unmatched_menus = Menu.objects.filter(standard_menu__isnull=True)[:limit]

        total = 0
        matched = 0

        for menu in unmatched_menus:
            total += 1
            result = self.match_menu(menu)
            if result:
                matched += 1

        return {"total": total, "matched": matched}
