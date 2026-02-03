from django.db import models


class Restaurant(models.Model):
    name = models.CharField(max_length=200, verbose_name="레스토랑명")
    address = models.TextField(blank=True, verbose_name="주소")
    phone = models.CharField(max_length=20, blank=True, verbose_name="전화번호")
    category = models.CharField(max_length=100, blank=True, verbose_name="카테고리")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "restaurants"
        verbose_name = "레스토랑"
        verbose_name_plural = "레스토랑 목록"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self):
        return self.name


class StandardMenu(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="표준 메뉴명")
    normalized_name = models.CharField(max_length=200, db_index=True, verbose_name="정규화된 메뉴명")
    category = models.CharField(max_length=100, blank=True, verbose_name="카테고리")
    description = models.TextField(blank=True, verbose_name="설명")

    # 메타데이터
    match_count = models.IntegerField(default=0, verbose_name="매칭 횟수")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "standard_menus"
        verbose_name = "표준 메뉴"
        verbose_name_plural = "표준 메뉴 목록"
        ordering = ["-match_count", "name"]
        indexes = [
            models.Index(fields=["normalized_name"]),
            models.Index(fields=["-match_count"]),
            models.Index(fields=["is_active", "-match_count"]),
        ]

    def __str__(self):
        return self.name

    def increment_match_count(self):
        """매칭 횟수 증가"""
        self.match_count += 1
        self.save(update_fields=["match_count", "updated_at"])


class Menu(models.Model):
    original_name = models.CharField(max_length=300, verbose_name="원본 메뉴명")
    normalized_name = models.CharField(max_length=300, db_index=True, verbose_name="정규화된 메뉴명")
    standard_menu = models.ForeignKey(
        StandardMenu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menus",
        verbose_name="표준 메뉴",
    )

    # 메뉴 정보
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menus",
        verbose_name="레스토랑",
    )
    price = models.IntegerField(null=True, blank=True, verbose_name="가격")
    description = models.TextField(blank=True, verbose_name="메뉴 설명")

    # 매칭 정보
    match_confidence = models.FloatField(null=True, blank=True, verbose_name="매칭 신뢰도 (0-1)")
    match_method = models.CharField(
        max_length=50,
        choices=[
            ("exact", "정확 일치"),
            ("mecab", "형태소 분석"),
            ("fasttext", "FastText"),
            ("manual", "수동 매칭"),
        ],
        default="mecab",
        verbose_name="매칭 방법",
    )
    is_verified = models.BooleanField(default=False, verbose_name="검증 여부")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "menus"
        verbose_name = "메뉴"
        verbose_name_plural = "메뉴 목록"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restaurant", "-created_at"]),
            models.Index(fields=["normalized_name"]),
            models.Index(fields=["standard_menu", "-created_at"]),
            models.Index(fields=["is_verified"]),
        ]
        unique_together = [["restaurant", "original_name"]]

    def __str__(self):
        return f"{self.original_name} ({self.restaurant.name})"


class MenuMatchingHistory(models.Model):
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="matching_histories",
        verbose_name="메뉴",
    )
    standard_menu = models.ForeignKey(
        StandardMenu,
        on_delete=models.CASCADE,
        related_name="matching_histories",
        verbose_name="표준 메뉴",
    )

    # 매칭 정보
    confidence_score = models.FloatField(verbose_name="신뢰도 점수")
    match_method = models.CharField(max_length=50, verbose_name="매칭 방법")
    matched_tokens = models.JSONField(default=list, verbose_name="매칭된 토큰")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        db_table = "menu_matching_histories"
        verbose_name = "메뉴 매칭 이력"
        verbose_name_plural = "메뉴 매칭 이력 목록"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["menu", "-created_at"]),
            models.Index(fields=["standard_menu", "-created_at"]),
            models.Index(fields=["-confidence_score"]),
        ]

    def __str__(self):
        return f"{self.menu.original_name} -> {self.standard_menu.name} ({self.confidence_score})"
