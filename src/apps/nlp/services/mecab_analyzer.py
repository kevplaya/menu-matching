import logging
import os
from typing import List, Optional, Tuple

from django.conf import settings

import MeCab

logger = logging.getLogger(__name__)

# 한글 mecab-ko-dic 후보 경로 (일본어 ipadic 대신 사용)
MECAB_KO_DIC_CANDIDATES = [
    "/usr/local/lib/mecab/dic/mecab-ko-dic",
    "/usr/lib/mecab/dic/mecab-ko-dic",
    "/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ko-dic",
]


def _collect_dic_paths(dic_path: Optional[str]) -> List[Optional[str]]:
    """시도할 사전 경로 목록: 설정값 → 한글 사전 후보 → None(기본=ipadic)."""
    paths: List[Optional[str]] = []
    if dic_path:
        paths.append(dic_path)
    for p in MECAB_KO_DIC_CANDIDATES:
        if p not in paths and os.path.isdir(p):
            paths.append(p)
    paths.append(None)  # 기본 사전
    return paths


class MecabAnalyzer:
    def __init__(self, dic_path: Optional[str] = None):
        """
        Args:
            dic_path: Mecab 사전 경로. 없으면 MECAB_DIC_PATH, 그다음 한글 사전 후보를 시도합니다.
        """
        if MeCab is None:
            raise ImportError("MeCab is not installed. Please install mecab-python3")

        dic_path = dic_path or getattr(settings, "MECAB_DIC_PATH", None)
        paths_to_try = _collect_dic_paths(dic_path)
        self.tagger = None
        last_error = None

        for path in paths_to_try:
            try:
                if path:
                    self.tagger = MeCab.Tagger(f"-d {path}")
                    logger.info("MeCab 초기화 성공: 사전 경로=%s", path)
                else:
                    self.tagger = MeCab.Tagger()
                    logger.info("MeCab 초기화 성공: 기본 사전(ipadic)")
                break
            except RuntimeError as e:
                last_error = e
                logger.debug("MeCab 사전 시도 실패 path=%s: %s", path, e)
                continue

        if self.tagger is None:
            logger.error(
                "MeCab 모든 경로 실패. 시도한 경로=%s, 마지막 에러=%s",
                paths_to_try,
                last_error,
            )
            raise RuntimeError(
                "MeCab could not be initialized. "
                "Install mecab-ko-dic or set MECAB_DIC_PATH to a valid dictionary path. "
                f"Last error: {last_error}"
            )

    def parse(self, text: str) -> List[Tuple[str, str]]:
        """
        텍스트를 형태소 분석합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            (형태소, 품사) 튜플의 리스트
        """
        if not text:
            return []

        result = []
        parsed = self.tagger.parse(text)

        for line in parsed.split("\n"):
            if line == "EOS" or not line:
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            surface = parts[0]  # 형태소
            features = parts[1].split(",")
            pos = features[0] if features else "Unknown"  # 품사

            result.append((surface, pos))

        return result

    def extract_nouns(self, text: str) -> List[str]:
        """
        텍스트에서 명사만 추출합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            명사 리스트
        """
        morphs = self.parse(text)
        nouns = []

        for surface, pos in morphs:
            # 명사 품사 태그: NNG(일반 명사), NNP(고유 명사), NNB(의존 명사)
            if pos.startswith("NN"):
                nouns.append(surface)

        return nouns

    def extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드를 추출합니다.
        명사, 동사, 형용사를 추출합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            키워드 리스트
        """
        morphs = self.parse(text)
        keywords = []

        for surface, pos in morphs:
            # 명사(NN), 동사(VV), 형용사(VA)
            if pos.startswith(("NN", "VV", "VA")):
                keywords.append(surface)

        return keywords

    def get_noun_tokens(self, text: str, min_length: int = 2) -> List[str]:
        """
        텍스트에서 지정된 길이 이상의 명사만 추출합니다.

        Args:
            text: 분석할 텍스트
            min_length: 최소 형태소 길이

        Returns:
            명사 리스트
        """
        nouns = self.extract_nouns(text)
        return [noun for noun in nouns if len(noun) >= min_length]
