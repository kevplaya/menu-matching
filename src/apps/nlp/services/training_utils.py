import csv
import logging
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

COMMON_VARIANTS = [
    "자장면",
    "짜장면",
    "간짜장",
    "쟁반짜장",
    "김치찌게",
    "김치찌개",
    "된장찌게",
    "된장찌개",
    "부대찌게",
    "부대찌개",
    "돈카스",
    "돈까스",
    "마르게리따피자",
    "마르게리타피자",
    "후라이드",
    "후라이드치킨",
    "후라이드 치킨",
    "양념치킨",
    "양념 치킨",
    "간장치킨",
    "마늘치킨",
    "허니버터치킨",
    "비빔밥",
    "비빔 밥",
    "돌솥비빔밥",
    "제육볶음",
    "제육 덮밥",
    "김치볶음밥",
    "불고기",
    "불고기버거",
    "갈비탕",
    "삼계탕",
    "페퍼로니피자",
    "페퍼로니 피자",
    "콤비네이션피자",
    "치즈피자",
    "포테이토피자",
    "쉬림프피자",
    "하와이안피자",
    "까르보나라",
    "로제파스타",
    "리조또",
    "시저샐러드",
    "치즈버거",
    "더블치즈버거",
    "감자튀김",
    "치킨너겟",
    "아메리카노",
    "카페라떼",
    "우동",
    "해물우동",
    "초밥",
    "모듬초밥",
    "회덮밥",
    "라멘",
    "가츠동",
    "카레라이스",
    "떡볶이",
    "매운떡볶이",
    "순대",
    "김밥",
    "참치김밥",
    "냉면",
    "물냉면",
    "비빔냉면",
    "칼국수",
    "수제비",
    "닭갈비",
    "춘천닭갈비",
    "족발",
    "보쌈",
    "낙지볶음",
    "쭈꾸미볶음",
    "파전",
    "해물파전",
    "김치전",
]


def _space_variants(line: str) -> Set[str]:
    out: Set[str] = set()
    if not line or " " in line:
        return out
    no_space = line.replace(" ", "")
    if no_space != line:
        out.add(no_space)
    if len(line) == 3:
        out.add(line[0] + " " + line[1:])
    elif len(line) == 4:
        out.add(line[:2] + " " + line[2:])
    return out


def prepare_training_data(
    output_path: str,
    include_menu_data: bool = False,
    project_root: Optional[Path] = None,
) -> int:
    """Build FastText training file from StandardMenu, optional Menu, CSV, and synthetic variants."""
    try:
        from django.conf import settings

        from apps.menus.models import Menu, StandardMenu
        from apps.nlp.services.normalizer import MenuNormalizer
    except ImportError as e:
        raise ImportError("Django models not available. Run via Django context.") from e

    root = project_root or getattr(settings, "PROJECT_ROOT", None)
    if isinstance(root, str):
        root = Path(root)

    collected: Set[str] = set()

    for menu in StandardMenu.objects.filter(is_active=True):
        name = menu.normalized_name.strip()
        if name and len(name) >= 2:
            collected.add(name)

    if include_menu_data:
        for menu in Menu.objects.all():
            name = menu.normalized_name.strip()
            if name and len(name) >= 2:
                collected.add(name)

    csv_path = root / "data" / "sample_menus.csv" if root else None
    if csv_path and csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw = row.get("original_name", "").strip()
                if not raw:
                    continue
                name = MenuNormalizer.normalize(raw).strip()
                if name and len(name) >= 2:
                    collected.add(name)

    for s in COMMON_VARIANTS:
        t = s.strip()
        if t and len(t) >= 2:
            collected.add(t)

    expanded: Set[str] = set(collected)
    for line in collected:
        expanded.update(_space_variants(line))
    for line in collected:
        no_space = line.replace(" ", "")
        if no_space and no_space != line:
            expanded.add(no_space)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for name in sorted(expanded):
            if name:
                f.write(f"{name}\n")

    logger.info("Training data: %d samples -> %s", len(expanded), output_path)
    return len(expanded)


def augment_training_data(input_path: str, output_path: str) -> int:
    """Add space/no-space variants for each line."""
    count = 0
    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            original = line.strip()
            if not original:
                continue
            fout.write(f"{original}\n")
            count += 1
            no_space = original.replace(" ", "")
            if no_space != original:
                fout.write(f"{no_space}\n")
                count += 1
    logger.info("Augmented: %d samples", count)
    return count


def validate_training_data(file_path: str) -> dict:
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Training data file not found: {file_path}")

    line_count = 0
    total_length = 0
    min_length = float("inf")
    max_length = 0
    empty_lines = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                empty_lines += 1
                continue
            line_count += 1
            length = len(stripped)
            total_length += length
            min_length = min(min_length, length)
            max_length = max(max_length, length)

    avg_length = total_length / line_count if line_count > 0 else 0
    return {
        "line_count": line_count,
        "avg_length": round(avg_length, 2),
        "min_length": min_length if min_length != float("inf") else 0,
        "max_length": max_length,
        "empty_lines": empty_lines,
    }
