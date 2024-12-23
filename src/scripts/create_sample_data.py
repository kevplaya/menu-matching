import os
import sys

import django

from apps.menus.models import Menu, StandardMenu
from apps.menus.services import MenuMatchingService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def create_standard_menus():
    """표준 메뉴 생성"""
    standard_menus = [
        # 한식 찌개류
        ("김치찌개", "김치찌개", "한식-찌개"),
        ("된장찌개", "된장찌개", "한식-찌개"),
        ("순두부찌개", "순두부찌개", "한식-찌개"),
        ("부대찌개", "부대찌개", "한식-찌개"),
        ("청국장", "청국장", "한식-찌개"),
        # 한식 밥류
        ("비빔밥", "비빔밥", "한식-밥"),
        ("돌솥비빔밥", "돌솥비빔밥", "한식-밥"),
        ("김치볶음밥", "김치볶음밥", "한식-밥"),
        ("제육덮밥", "제육덮밥", "한식-밥"),
        # 한식 고기
        ("삼겹살", "삼겹살", "한식-고기"),
        ("목살", "목살", "한식-고기"),
        ("갈비", "갈비", "한식-고기"),
        ("불고기", "불고기", "한식-고기"),
        # 중식
        ("짜장면", "짜장면", "중식"),
        ("짬뽕", "짬뽕", "중식"),
        ("탕수육", "탕수육", "중식"),
        ("볶음밥", "볶음밥", "중식"),
        # 치킨
        ("치킨", "치킨", "치킨"),
        ("후라이드치킨", "후라이드치킨", "치킨"),
        ("양념치킨", "양념치킨", "치킨"),
        ("간장치킨", "간장치킨", "치킨"),
        ("두마리치킨", "두마리치킨", "치킨"),
        ("반반치킨", "반반치킨", "치킨"),
        ("순살치킨", "순살치킨", "치킨"),
    ]

    print("Creating standard menus...")
    for name, normalized, category in standard_menus:
        StandardMenu.objects.get_or_create(
            name=name,
            defaults={"normalized_name": normalized, "category": category},
        )
    print(f"✓ Created {len(standard_menus)} standard menus")


def create_sample_menus():
    """샘플 메뉴 생성 및 매칭"""
    sample_menus = [
        # 다양한 형태의 김치찌개
        ("얼큰 김치찌개 1인분", "REST001", 8000),
        ("김치찌개(特)", "REST002", 9000),
        ("돼지고기 김치찌개", "REST003", 8500),
        ("김치찌개 2인분", "REST001", 15000),
        # 된장찌개
        ("구수한 된장찌개", "REST001", 7000),
        ("된장찌개 [추천]", "REST002", 7500),
        # 비빔밥
        ("석쇠 비빔밥", "REST004", 9000),
        ("비빔밥 (야채 많이)", "REST004", 9000),
        ("돌솥비빔밥 大", "REST005", 10000),
        # 삼겹살
        ("한돈 삼겹살 200g", "REST006", 13000),
        ("삼겹살 구이", "REST006", 12000),
        # 치킨
        ("후라이드 치킨 (순살)", "REST007", 16000),
        ("양념 치킨", "REST007", 17000),
        # 중식
        ("간짜장", "REST008", 6000),
        ("해물 짬뽕", "REST008", 8000),
        ("탕수육 (소)", "REST008", 15000),
    ]

    print("\nCreating and matching sample menus...")
    service = MenuMatchingService()

    for original_name, restaurant_id, price in sample_menus:
        menu = service.create_and_match_menu(
            original_name=original_name,
            restaurant_id=restaurant_id,
            price=price,
        )
        match_status = "✓ MATCHED" if menu.standard_menu else "✗ NOT MATCHED"
        confidence = f"({menu.match_confidence:.2f})" if menu.match_confidence else ""
        print(
            f"{match_status} {confidence}: {original_name} -> "
            f"{menu.standard_menu.name if menu.standard_menu else 'None'}"
        )

    print(f"\n✓ Created {len(sample_menus)} sample menus")


def print_statistics():
    """통계 출력"""
    total_menus = Menu.objects.count()
    matched_menus = Menu.objects.filter(standard_menu__isnull=False).count()
    match_rate = (matched_menus / total_menus * 100) if total_menus > 0 else 0

    print("\n" + "=" * 50)
    print("📊 Statistics")
    print("=" * 50)
    print(f"Total Standard Menus: {StandardMenu.objects.count()}")
    print(f"Total Menus: {total_menus}")
    print(f"Matched Menus: {matched_menus}")
    print(f"Match Rate: {match_rate:.1f}%")
    print("=" * 50)


if __name__ == "__main__":
    print("🚀 Starting sample data creation...")
    print()

    create_standard_menus()
    create_sample_menus()
    print_statistics()

    print("\n✅ Sample data creation completed!")
    print("\nYou can now:")
    print("  - Access API: http://localhost:8000/api/menus/")
    print("  - Access Admin: http://localhost:8000/admin/")
    print("  - View API Docs: http://localhost:8000/api/docs/")
