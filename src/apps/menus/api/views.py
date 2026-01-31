from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.menus.api.serializers import (
    MenuBatchMatchRequestSerializer,
    MenuCreateSerializer,
    MenuMatchingHistorySerializer,
    MenuMatchRequestSerializer,
    MenuMatchResponseSerializer,
    MenuSerializer,
    RematchResultSerializer,
    RestaurantSerializer,
    StandardMenuSerializer,
)
from apps.menus.models import Menu, MenuMatchingHistory, Restaurant, StandardMenu
from apps.menus.services import MenuMatchingService


@extend_schema_view(
    list=extend_schema(summary="레스토랑 목록 조회", tags=["Restaurant"]),
    retrieve=extend_schema(summary="레스토랑 상세 조회", tags=["Restaurant"]),
    create=extend_schema(summary="레스토랑 생성", tags=["Restaurant"]),
    update=extend_schema(summary="레스토랑 수정", tags=["Restaurant"]),
    partial_update=extend_schema(summary="레스토랑 부분 수정", tags=["Restaurant"]),
    destroy=extend_schema(summary="레스토랑 삭제", tags=["Restaurant"]),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "address"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    @extend_schema(
        summary="레스토랑의 메뉴 목록 조회",
        description="특정 레스토랑의 모든 메뉴를 조회합니다.",
        tags=["Restaurant"],
    )
    @action(detail=True, methods=["get"])
    def menus(self, request, pk=None):
        """레스토랑의 메뉴 목록"""
        restaurant = self.get_object()
        menus = Menu.objects.filter(restaurant=restaurant).select_related("standard_menu")
        serializer = MenuSerializer(menus, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="표준 메뉴 목록 조회", tags=["StandardMenu"]),
    retrieve=extend_schema(summary="표준 메뉴 상세 조회", tags=["StandardMenu"]),
    create=extend_schema(summary="표준 메뉴 생성", tags=["StandardMenu"]),
    update=extend_schema(summary="표준 메뉴 수정", tags=["StandardMenu"]),
    partial_update=extend_schema(summary="표준 메뉴 부분 수정", tags=["StandardMenu"]),
    destroy=extend_schema(summary="표준 메뉴 삭제", tags=["StandardMenu"]),
)
class StandardMenuViewSet(viewsets.ModelViewSet):
    queryset = StandardMenu.objects.all()
    serializer_class = StandardMenuSerializer
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "normalized_name", "description"]
    ordering_fields = ["match_count", "created_at", "name"]
    ordering = ["-match_count"]

    @extend_schema(
        summary="인기 표준 메뉴 조회",
        description="매칭 횟수가 많은 상위 표준 메뉴를 조회합니다.",
        parameters=[OpenApiParameter(name="limit", type=int, default=10, description="조회할 메뉴 개수")],
        tags=["StandardMenu"],
    )
    @action(detail=False, methods=["get"])
    def popular(self, request):
        """인기 표준 메뉴 목록 (매칭 횟수 기준)"""
        limit = int(request.query_params.get("limit", 10))
        menus = StandardMenu.objects.filter(is_active=True).order_by("-match_count")[:limit]
        serializer = self.get_serializer(menus, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="메뉴 목록 조회", tags=["Menu"]),
    retrieve=extend_schema(summary="메뉴 상세 조회", tags=["Menu"]),
    create=extend_schema(summary="메뉴 생성 및 자동 매칭", tags=["Menu"]),
    update=extend_schema(summary="메뉴 수정", tags=["Menu"]),
    partial_update=extend_schema(summary="메뉴 부분 수정", tags=["Menu"]),
    destroy=extend_schema(summary="메뉴 삭제", tags=["Menu"]),
)
class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("standard_menu").all()
    serializer_class = MenuSerializer
    filterset_fields = ["restaurant_id", "match_method", "is_verified", "standard_menu"]
    search_fields = ["original_name", "normalized_name"]
    ordering_fields = ["created_at", "match_confidence"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return MenuCreateSerializer
        return MenuSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 메뉴 매칭 서비스 사용
        service = MenuMatchingService()
        menu = service.create_and_match_menu(
            original_name=serializer.validated_data["original_name"],
            restaurant=serializer.validated_data.get("restaurant"),
            restaurant_code=serializer.validated_data.get("restaurant_code", ""),
            price=serializer.validated_data.get("price"),
            description=serializer.validated_data.get("description", ""),
        )

        # 응답
        response_serializer = MenuSerializer(menu)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="메뉴 매칭 수행",
        description="단일 메뉴에 대해 표준 메뉴 매칭을 수행합니다.",
        request=MenuMatchRequestSerializer,
        responses={200: MenuMatchResponseSerializer},
        tags=["Menu"],
    )
    @action(detail=False, methods=["post"])
    def match(self, request):
        """메뉴 매칭 수행"""
        serializer = MenuMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = MenuMatchingService()
        menu = service.create_and_match_menu(
            original_name=serializer.validated_data["original_name"],
            restaurant=serializer.validated_data.get("restaurant"),
            restaurant_code=serializer.validated_data.get("restaurant_code", ""),
            price=serializer.validated_data.get("price"),
            description=serializer.validated_data.get("description", ""),
        )

        response_data = {
            "menu": menu,
            "matched": menu.standard_menu is not None,
            "standard_menu": menu.standard_menu,
            "confidence": menu.match_confidence,
            "method": menu.match_method,
        }

        response_serializer = MenuMatchResponseSerializer(response_data)
        return Response(response_serializer.data)

    @extend_schema(
        summary="메뉴 일괄 매칭",
        description="여러 메뉴에 대해 일괄적으로 표준 메뉴 매칭을 수행합니다.",
        request=MenuBatchMatchRequestSerializer,
        responses={200: MenuMatchResponseSerializer(many=True)},
        tags=["Menu"],
    )
    @action(detail=False, methods=["post"])
    def batch_match(self, request):
        """메뉴 일괄 매칭"""
        serializer = MenuBatchMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = MenuMatchingService()
        results = []

        for menu_data in serializer.validated_data["menus"]:
            menu = service.create_and_match_menu(
                original_name=menu_data["original_name"],
                restaurant=menu_data.get("restaurant"),
                restaurant_code=menu_data.get("restaurant_code", ""),
                price=menu_data.get("price"),
                description=menu_data.get("description", ""),
            )

            results.append(
                {
                    "menu": menu,
                    "matched": menu.standard_menu is not None,
                    "standard_menu": menu.standard_menu,
                    "confidence": menu.match_confidence,
                    "method": menu.match_method,
                }
            )

        response_serializer = MenuMatchResponseSerializer(results, many=True)
        return Response(response_serializer.data)

    @extend_schema(
        summary="미매칭 메뉴 재매칭",
        description="표준 메뉴가 매칭되지 않은 메뉴들을 다시 매칭 시도합니다.",
        parameters=[
            OpenApiParameter(name="limit", type=int, default=100, description="처리할 최대 메뉴 개수")
        ],
        responses={200: RematchResultSerializer},
        tags=["Menu"],
    )
    @action(detail=False, methods=["post"])
    def rematch_unmatched(self, request):
        """미매칭 메뉴 재매칭"""
        limit = int(request.query_params.get("limit", 100))

        service = MenuMatchingService()
        result = service.rematch_unmatched_menus(limit=limit)

        result["success_rate"] = result["matched"] / result["total"] if result["total"] > 0 else 0.0

        serializer = RematchResultSerializer(result)
        return Response(serializer.data)

    @extend_schema(
        summary="음식점별 메뉴 조회",
        description="특정 음식점의 모든 메뉴를 조회합니다.",
        parameters=[
            OpenApiParameter(name="restaurant_id", type=str, required=True, description="음식점 ID")
        ],
        tags=["Menu"],
    )
    @action(detail=False, methods=["get"])
    def by_restaurant(self, request):
        """음식점별 메뉴 조회"""
        restaurant_code = request.query_params.get("restaurant_code")
        restaurant_id = request.query_params.get("restaurant_id")

        if not restaurant_code and not restaurant_id:
            return Response(
                {"error": "restaurant_code or restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if restaurant_id:
            menus = self.queryset.filter(restaurant_id=restaurant_id)
        else:
            menus = self.queryset.filter(restaurant_code=restaurant_code)

        serializer = self.get_serializer(menus, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="매칭 이력 목록 조회", tags=["MatchingHistory"]),
    retrieve=extend_schema(summary="매칭 이력 상세 조회", tags=["MatchingHistory"]),
)
class MenuMatchingHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuMatchingHistory.objects.select_related("menu", "standard_menu").all()
    serializer_class = MenuMatchingHistorySerializer
    filterset_fields = ["menu", "standard_menu", "match_method"]
    ordering_fields = ["created_at", "confidence_score"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="메뉴별 매칭 이력 조회",
        description="특정 메뉴의 매칭 이력을 조회합니다.",
        parameters=[OpenApiParameter(name="menu_id", type=int, required=True, description="메뉴 ID")],
        tags=["MatchingHistory"],
    )
    @action(detail=False, methods=["get"])
    def by_menu(self, request):
        """메뉴별 매칭 이력"""
        menu_id = request.query_params.get("menu_id")
        if not menu_id:
            return Response({"error": "menu_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        histories = self.queryset.filter(menu_id=menu_id)
        serializer = self.get_serializer(histories, many=True)
        return Response(serializer.data)
