# 표준 메뉴 매칭 서비스

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

 다양한 형태로 등록된 메뉴 이름을 Mecab 형태소 분석과 FastText 임베딩을 활용해 표준 메뉴로 자동 매칭합니다.

## 개요

### 문제 정의

배달 플랫폼에서 동일 메뉴가 다른 이름으로 등록되는 문제:
- "김치찌개 1인분" vs "얼큰 김치찌개" vs "김치찌개(특)"
- "삼겹살 200g" vs "삼겹살 구이" vs "한돈 삼겹살"

표준 메뉴로 통합해서 데이터 분석과 추천 시스템에 활용하는 것이 목표입니다.

### 주요 기능

- 메뉴 텍스트 정규화 (괄호, 수량, 특수문자 제거)
- 3단계 매칭 전략
  1. 정확 일치
  2. 형태소 분석 기반 유사도 (Mecab)
  3. 의미 벡터 기반 유사도 (FastText)
- REST API 제공
- 매칭 이력 및 신뢰도 관리
- 일괄 처리 지원

## 기술 스택

- Python 3.11, Django 4.2, Django REST Framework
- MySQL 8.0
- mecab-ko, FastText
- Docker, Docker Compose
- pytest, GitHub Actions
- Black, isort, flake8

## 시작하기

### 요구사항

- Docker & Docker Compose
- Git

### 설치

```bash
# 저장소 클론
git clone https://github.com/jihoon-lee/menu-matching.git
cd menu-matching

# 환경 변수 설정 (선택사항, 기본값 사용 가능)
cp .env.example .env

# Docker 실행 (마이그레이션 자동 실행)
docker-compose up -d

# 서비스 준비 대기 (약 10-15초)
# 표준 메뉴 및 관리자 계정이 자동으로 생성됩니다

# 접속
# API: http://localhost:8080/api/menus/
# Admin: http://localhost:8080/admin/ (admin/admin)
# Docs: http://localhost:8080/api/docs/
```

### 프론트엔드 실행 (선택사항)

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 접속
```

**참고:**
- 첫 실행 시 자동으로 24개의 표준 메뉴가 생성됩니다
- 관리자 계정: `admin` / `admin`
- DB 초기화: `docker-compose down -v && docker-compose up -d`

## API

### 엔드포인트

**표준 메뉴**

- `GET /api/menus/standard-menus/` - 표준 메뉴 목록 조회
- `POST /api/menus/standard-menus/` - 표준 메뉴 생성
- `GET /api/menus/standard-menus/{id}/` - 표준 메뉴 상세 조회
- `PUT/PATCH /api/menus/standard-menus/{id}/` - 표준 메뉴 수정
- `DELETE /api/menus/standard-menus/{id}/` - 표준 메뉴 삭제
- `GET /api/menus/standard-menus/popular/` - 인기 표준 메뉴 조회

**메뉴 매칭**

- `GET /api/menus/items/` - 메뉴 목록 조회
- `POST /api/menus/items/` - 메뉴 생성 (자동 매칭)
- `POST /api/menus/items/match/` - 단일 메뉴 매칭
- `POST /api/menus/items/batch_match/` - 일괄 메뉴 매칭
- `POST /api/menus/items/rematch_unmatched/` - 미매칭 메뉴 재매칭
- `GET /api/menus/items/by_restaurant/` - 음식점별 메뉴 조회

**매칭 이력**

- `GET /api/menus/matching-history/` - 매칭 이력 목록
- `GET /api/menus/matching-history/by_menu/` - 메뉴별 매칭 이력

### 사용 예제

표준 메뉴 생성:

```bash
curl -X POST http://localhost:8080/api/menus/standard-menus/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "김치찌개",
    "normalized_name": "김치찌개",
    "category": "한식",
    "description": "대표적인 한국 찌개 요리"
  }'
```

메뉴 생성 및 자동 매칭:

```bash
curl -X POST http://localhost:8080/api/menus/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "original_name": "얼큰 김치찌개 1인분",
    "restaurant_id": "REST001",
    "price": 8000,
    "description": "돼지고기 김치찌개"
  }'
```

일괄 매칭:

```bash
curl -X POST http://localhost:8080/api/menus/items/batch_match/ \
  -H "Content-Type: application/json" \
  -d '{
    "menus": [
      {
        "original_name": "김치찌개",
        "restaurant_id": "REST001",
        "price": 8000
      },
      {
        "original_name": "된장찌개",
        "restaurant_id": "REST001",
        "price": 7000
      }
    ]
  }'
```

## 테스트

```bash
# Docker 환경에서 테스트
docker-compose exec web pytest
```

## Docker에서 스크립트 실행

로컬에서 `python manage.py runserver`가 동작하지 않을 때는 Docker 컨테이너 안에서 실행하세요.

```bash
# 표준 메뉴 + 샘플 메뉴 생성
docker-compose exec web bash -c "cd /app/src && python scripts/create_sample_data.py"

# 테스트
docker-compose exec web pytest
```

## FastText 학습

1. 표준 메뉴가 DB에 있어야 합니다. 없으면 위의 샘플 데이터 생성으로 먼저 만드세요.
2. 학습 데이터는 `StandardMenu` + `data/sample_menus.csv` 정규화 결과 + 자주 쓰는 메뉴 변형(자장면/짜장면 등)으로 자동 생성됩니다.
3. 학습 후 `models/menu.bin`이 생성되면 웹 서버를 재시작하면 3단계 매칭(FastText)에서 사용됩니다.

```bash
docker-compose exec web python manage.py train_fasttext
docker-compose restart web
```

## 프로젝트 구조

```
menu-matching/
├── .github/
│   └── workflows/
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/   # React 컴포넌트
│   │   ├── api/          # API 클라이언트
│   │   ├── App.jsx       # 메인 앱
│   │   └── main.jsx      # 엔트리 포인트
│   ├── package.json
│   └── vite.config.js
├── src/
│   ├── config/
│   ├── apps/
│   │   ├── menus/
│   │   │   ├── api/
│   │   │   ├── tests/
│   │   │   ├── migrations/
│   │   └── nlp/
│   │       ├── services/
│   └── scripts/
├── data/
```

## MeCab 한글 사전

형태소 분석에는 **한글 사전(mecab-ko-dic)** 이 필요합니다. 일본어 사전(ipadic)만 있으면 한글 메뉴명이 제대로 분석되지 않아 매칭이 되지 않습니다.

- **Docker**: 이미지 빌드 시 mecab-ko-dic이 설치되며, 앱이 `/usr/local/lib/mecab/dic/mecab-ko-dic` 등을 자동으로 사용합니다.
- **로컬 실행**: mecab-ko-dic을 설치한 뒤, 설치 경로가 다르면 `MECAB_DIC_PATH` 환경 변수로 지정하세요.
  예: `export MECAB_DIC_PATH=/usr/local/lib/mecab/dic/mecab-ko-dic`

## 매칭 알고리즘

### 매칭 프로세스

```
1. 텍스트 정규화
   - 괄호, 특수문자, 수량 제거
   - 소문자 변환 및 공백 정리

2. Exact Match
   - 정규화된 이름으로 표준 메뉴 검색
   - 신뢰도: 1.0

3. Mecab 기반 매칭
   - 명사 추출 및 비교
   - 공통 명사 비율로 유사도 계산
   - 신뢰도: 0.6 ~ 1.0

4. FastText 기반 매칭
   - 임베딩 벡터 변환
   - 코사인 유사도 계산
   - 신뢰도: 0.7 ~ 1.0
```

## 향후 계획

- Redis 캐싱
- AWS SNS/SQS 연동
- FastText 학습 파이프라인
- Elasticsearch 연동
- Kubernetes 배포

## 프론트엔드

React + Material-UI로 구현된 웹 인터페이스를 제공합니다.

### 실행 방법

```bash
# 백엔드 실행
docker-compose up -d

# 프론트엔드 실행 (별도 터미널)
cd frontend
npm install
npm run dev

# 접속: http://localhost:5173
```

### 주요 기능

- **레스토랑 관리**: 레스토랑 추가 및 목록 조회
- **메뉴 관리**: 레스토랑별 메뉴 추가 및 자동/수동 매칭
- **매칭 결과 확인**: 표준 메뉴별 매칭 현황 및 신뢰도 확인
- **표준 메뉴 관리**: 표준 메뉴 CRUD 및 통계

자세한 내용은 [frontend/README.md](frontend/README.md)를 참고하세요.

### 마일스톤

| 단계 | 날짜 | 내용 |
|------|------|------|
| 초기화 | 2024-12-20 | Git, Django, Docker |
| 모델 | 2024-12-21 | DB 스키마 |
| NLP | 2024-12-22 | 매칭 로직 |
| API | 2024-12-22 | DRF 엔드포인트 |
| CI/CD | 2024-12-22 | GitHub Actions |
| 리팩토링 | 2024-12-23 | DRF 구조 개선 및 리팩토링 |
| 프론트엔드 | 2026-01-31 | React + Material-UI 웹 인터페이스 |
