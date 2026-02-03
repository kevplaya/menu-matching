import re
from typing import List


class MenuNormalizer:
    REMOVE_PATTERNS = [
        r"\(.*?\)",  # 괄호 안의 내용
        r"\[.*?\]",  # 대괄호 안의 내용
        r"<.*?>",  # 꺾쇠괄호 안의 내용
        r"\d+인분",  # N인분
        r"\d+개입",  # N개입
        r"\d+g",  # N그램
        r"\d+ml",  # N밀리리터
        r"\d+L",  # N리터
        r"[0-9,]+원",  # 가격 (콤마 포함 먼저)
        r"[0-9]+원",
    ]

    REPLACE_PATTERNS = [
        (r"\s+", " "),
        (r"[^\w\s가-힣]", " "),
    ]

    # 제거할 키워드들
    REMOVE_KEYWORDS = [
        "세트",
        "특",
        "大",
        "中",
        "小",
        "대",
        "중",
        "소",
        "신메뉴",
        "추천",
        "인기",
        "best",
        "new",
        "hot",
    ]

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        메뉴 텍스트를 정규화합니다.

        Args:
            text: 원본 메뉴 텍스트

        Returns:
            정규화된 메뉴 텍스트
        """
        if not text:
            return ""

        # 소문자 변환
        normalized = text.lower()

        # 패턴 제거
        for pattern in cls.REMOVE_PATTERNS:
            normalized = re.sub(pattern, "", normalized)

        # 패턴 대체
        for pattern, replacement in cls.REPLACE_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized)

        # 키워드 제거
        for keyword in cls.REMOVE_KEYWORDS:
            normalized = normalized.replace(keyword.lower(), " ")

        # 앞뒤 공백 제거 및 중복 공백 정리
        normalized = " ".join(normalized.split())

        return normalized.strip()

    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """
        메뉴 텍스트에서 키워드를 추출합니다.

        Args:
            text: 원본 메뉴 텍스트

        Returns:
            키워드 리스트
        """
        normalized = cls.normalize(text)
        if not normalized:
            return []

        # 공백으로 분리
        keywords = normalized.split()

        # 2글자 이상인 키워드만 반환
        return [kw for kw in keywords if len(kw) >= 2]
