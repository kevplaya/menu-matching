# 표준 메뉴 매칭 서비스 - 프론트엔드

React + Material-UI로 구현된 메뉴 매칭 서비스 웹 인터페이스입니다.

## 기술 스택

- React 18
- Vite
- Material-UI (MUI) v5
- React Router v6
- Axios

## 시작하기

### 의존성 설치

```bash
cd frontend
npm install
```

### 개발 서버 실행

```bash
npm run dev
```

개발 서버는 `http://localhost:5173`에서 실행됩니다.

### 빌드

```bash
npm run build
```

## 주요 기능

### 1. 레스토랑 관리
- 레스토랑 목록 조회
- 레스토랑 추가
- 레스토랑 상세 정보 확인

### 2. 메뉴 관리
- 레스토랑별 메뉴 추가
- 자동 표준 메뉴 매칭
- 수동 표준 메뉴 매칭
- 매칭 결과 확인 (신뢰도, 매칭 방법)

### 3. 매칭된 메뉴 확인
- 표준 메뉴별로 그룹화된 뷰
- 레스토랑별 매칭 현황
- 매칭 신뢰도 표시

### 4. 표준 메뉴 관리
- 표준 메뉴 CRUD
- 매칭 횟수 통계

## 화면 구성

- `/restaurants` - 레스토랑 목록
- `/restaurants/:id` - 레스토랑 상세 및 메뉴 관리
- `/matched-menus` - 표준 메뉴별 매칭 현황
- `/standard-menus` - 표준 메뉴 관리
