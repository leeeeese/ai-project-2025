"""
LangGraph State 정의
중고거래 추천 시스템의 전역 상태를 관리합니다.
"""

from typing import TypedDict, List, Optional, Dict, Any
from enum import Enum


class PersonaType(str, Enum):
    """페르소나 타입 정의"""
    LOCAL_OFFLINE = "local_offline"  # 동네직거래 오프라인형
    FAST_SHIPPING_ONLINE = "fast_shipping_online"  # 빠른배송 온라인형
    HYBRID_TRADE = "hybrid_trade"  # 하이브리드 거래형
    TRUST_SAFETY_PRO = "trust_safety_pro"  # 신뢰·안전 전문가형
    HIGH_QUALITY_NEW = "high_quality_new"  # 상태 최상·새상품형
    NICHE_SPECIALIST = "niche_specialist"  # 니치 전문상인형
    POWER_SELLER = "power_seller"  # 활동 파워셀러형
    NEGOTIATION_FRIENDLY = "negotiation_friendly"  # 가격흥정 친화형
    RESPONSIVE_KIND = "responsive_kind"  # 응답 신속·친절형
    BALANCED_LOW_ACTIVITY = "balanced_low_activity"  # 균형·저활동·주의형


class UserInput(TypedDict):
    """사용자 입력 데이터"""
    search_query: str  # 검색 쿼리
    price_min: Optional[float]  # 최소 가격
    price_max: Optional[float]  # 최대 가격
    category: Optional[str]  # 카테고리
    location: Optional[str]  # 지역
    user_id: Optional[str]  # 사용자 ID (기존 데이터가 있는 경우)


class PersonaVector(TypedDict):
    """5축 페르소나 벡터 (0-100 점수)"""
    trust_safety: float  # 신뢰·안전
    quality_condition: float  # 품질·상태
    remote_transaction: float  # 원격거래성향
    activity_responsiveness: float  # 활동·응답
    price_flexibility: float  # 가격유연성


class PersonaClassification(TypedDict):
    """페르소나 분류 결과"""
    persona_type: PersonaType
    confidence: float  # 분류 신뢰도 (0-1)
    vector: PersonaVector  # 사용자 벡터
    matched_prototype: PersonaVector  # 매칭된 프로토타입 벡터


class SearchQuery(TypedDict):
    """생성된 검색 쿼리"""
    original_query: str  # 원본 쿼리
    enhanced_query: str  # 향상된 쿼리
    keywords: List[str]  # 추출된 키워드
    filters: Dict[str, Any]  # 필터 조건들


class ProductMatch(TypedDict):
    """상품 매칭 결과"""
    product_id: str
    seller_id: str
    title: str
    price: float
    category: str
    condition: str
    location: str
    match_score: float  # 매칭 점수
    persona_score: float  # 페르소나 매칭 점수


class RankingResult(TypedDict):
    """랭킹 결과"""
    products: List[ProductMatch]
    total_count: int
    ranking_criteria: List[str]  # 랭킹 기준들


class SQLQuery(TypedDict):
    """생성된 SQL 쿼리"""
    query: str
    parameters: Dict[str, Any]
    execution_time: Optional[float]


class RecommendationState(TypedDict):
    """LangGraph 전역 상태"""
    # 입력 데이터
    user_input: UserInput

    # Agent 실행 결과들
    persona_classification: Optional[PersonaClassification]
    search_query: Optional[SearchQuery]
    product_matches: Optional[List[ProductMatch]]
    ranking_result: Optional[RankingResult]
    sql_query: Optional[SQLQuery]

    # 실행 상태
    current_step: str  # 현재 실행 중인 단계
    completed_steps: List[str]  # 완료된 단계들
    error_message: Optional[str]  # 에러 메시지

    # 메타데이터
    session_id: str  # 세션 ID
    timestamp: float  # 타임스탬프
    execution_time: Optional[float]  # 전체 실행 시간


# 페르소나 프로토타입 정의 (persona_definition.md 기반)
PERSONA_PROTOTYPES = {
    PersonaType.LOCAL_OFFLINE: {
        "name": "동네직거래 오프라인형",
        "vector": {
            "trust_safety": 25,
            "quality_condition": 0,
            "remote_transaction": 0,
            "activity_responsiveness": 25,
            "price_flexibility": 50
        }
    },
    PersonaType.FAST_SHIPPING_ONLINE: {
        "name": "빠른배송 온라인형",
        "vector": {
            "trust_safety": 75,
            "quality_condition": 25,
            "remote_transaction": 75,
            "activity_responsiveness": 50,
            "price_flexibility": 25
        }
    },
    PersonaType.HYBRID_TRADE: {
        "name": "하이브리드 거래형",
        "vector": {
            "trust_safety": 50,
            "quality_condition": 50,
            "remote_transaction": 50,
            "activity_responsiveness": 50,
            "price_flexibility": 50
        }
    },
    PersonaType.TRUST_SAFETY_PRO: {
        "name": "신뢰·안전 전문가형",
        "vector": {
            "trust_safety": 100,
            "quality_condition": 50,
            "remote_transaction": 50,
            "activity_responsiveness": 75,
            "price_flexibility": 25
        }
    },
    PersonaType.HIGH_QUALITY_NEW: {
        "name": "상태 최상·새상품형",
        "vector": {
            "trust_safety": 50,
            "quality_condition": 100,
            "remote_transaction": 25,
            "activity_responsiveness": 50,
            "price_flexibility": 25
        }
    },
    PersonaType.NICHE_SPECIALIST: {
        "name": "니치 전문상인형",
        "vector": {
            "trust_safety": 50,
            "quality_condition": 75,
            "remote_transaction": 50,
            "activity_responsiveness": 50,
            "price_flexibility": 25
        }
    },
    PersonaType.POWER_SELLER: {
        "name": "활동 파워셀러형",
        "vector": {
            "trust_safety": 50,
            "quality_condition": 50,
            "remote_transaction": 50,
            "activity_responsiveness": 100,
            "price_flexibility": 25
        }
    },
    PersonaType.NEGOTIATION_FRIENDLY: {
        "name": "가격흥정 친화형",
        "vector": {
            "trust_safety": 25,
            "quality_condition": 25,
            "remote_transaction": 25,
            "activity_responsiveness": 25,
            "price_flexibility": 100
        }
    },
    PersonaType.RESPONSIVE_KIND: {
        "name": "응답 신속·친절형",
        "vector": {
            "trust_safety": 75,
            "quality_condition": 50,
            "remote_transaction": 50,
            "activity_responsiveness": 100,
            "price_flexibility": 25
        }
    },
    PersonaType.BALANCED_LOW_ACTIVITY: {
        "name": "균형·저활동·주의형",
        "vector": {
            "trust_safety": 50,
            "quality_condition": 50,
            "remote_transaction": 50,
            "activity_responsiveness": 25,
            "price_flexibility": 50
        }
    }
}

# 매칭 가중치 정의
MATCHING_WEIGHTS = {
    "trust_safety": 0.24,
    "quality_condition": 0.18,
    "remote_transaction": 0.18,
    "activity_responsiveness": 0.22,
    "price_flexibility": 0.18
}
