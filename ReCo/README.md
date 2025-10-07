# ReCo - 중고거래 추천 시스템

LangGraph Agent 기반의 중고거래 상품 추천 시스템입니다.

## 🏗️ 아키텍처

```
ReCo/
├── main.py                    # FastAPI 웹 서버 + LangGraph 오케스트레이터
├── src/
│   ├── core/
│   │   ├── state.py          # LangGraph State 정의
│   │   ├── config.py         # 설정 관리
│   │   └── database.py       # DB 연결 (MySQL + PostgreSQL)
│   ├── agents/
│   │   ├── persona_classifier.py    # 페르소나 분류 Agent
│   │   ├── query_generator.py       # 검색 쿼리 생성 Agent
│   │   ├── product_matching.py      # 상품 매칭 Agent
│   │   ├── ranker.py               # 랭킹 Agent
│   │   └── router.py               # 라우터 Agent
│   ├── graphs/
│   │   └── recommendation_graph.py  # LangGraph 정의
│   └── api/
│       ├── routes.py         # FastAPI 라우트
│       └── schemas.py        # Pydantic 모델
├── playbook/                 # 페르소나 정의서
└── requirements.txt
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 3. 데이터베이스 설정

- **MySQL**: 기존 상품/판매자 데이터 저장
- **PostgreSQL**: LangGraph State 저장

### 4. 서버 실행

```bash
python main.py
```

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

## 📚 API 사용법

### 1. 상품 추천

```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "아이폰 14",
    "price_min": 1000000,
    "price_max": 1500000,
    "category": "스마트폰",
    "location": "서울"
  }'
```

### 2. 페르소나 목록 조회

```bash
curl "http://localhost:8000/api/v1/personas"
```

### 3. 헬스 체크

```bash
curl "http://localhost:8000/api/v1/health"
```

## 🔄 워크플로우

1. **사용자 입력** → 검색 쿼리, 가격 범위, 카테고리 등
2. **페르소나 분류** → 사용자 특성을 10가지 페르소나로 분류
3. **검색 쿼리 생성** → 페르소나에 맞게 쿼리 향상
4. **상품 매칭** → 텍스트 매칭 + 페르소나 매칭
5. **랭킹** → 최종 추천 상품 순서 결정

## 🧠 페르소나 시스템

10가지 페르소나를 5축으로 분류:

- **신뢰·안전** (Trust & Safety)
- **품질·상태** (Quality & Condition)
- **원격거래성향** (Remote Transaction Preference)
- **활동·응답** (Activity & Responsiveness)
- **가격유연성** (Price Flexibility)

## 🛠️ 개발

### Agent 추가

1. `src/agents/`에 새 Agent 파일 생성
2. `src/graphs/recommendation_graph.py`에 노드 추가
3. 라우터에서 조건부 엣지 설정

### State 확장

`src/core/state.py`에서 `RecommendationState`를 수정하여 새로운 상태 필드 추가

## 📝 TODO

- [ ] 실제 MySQL 데이터베이스 연동
- [ ] 사용자 벡터 생성 로직 구현
- [ ] SQL 쿼리 생성 Agent 구현
- [ ] 웹 프론트엔드 구현
- [ ] 로깅 및 모니터링 추가
- [ ] 단위 테스트 작성
