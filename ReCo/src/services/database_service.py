"""
데이터베이스 서비스
판매자와 상품 데이터를 조회합니다.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from ..core.config import get_mysql_url


class DatabaseService:
    """데이터베이스 서비스"""

    def __init__(self):
        self.engine = create_engine(get_mysql_url())

    def get_sellers_with_persona(self, limit: int = 100) -> List[Dict[str, Any]]:
        """페르소나 정보가 있는 판매자들 조회"""
        query = """
        SELECT 
            seller_id,
            seller_name,
            trust_safety,
            quality_condition,
            remote_transaction,
            activity_responsiveness,
            price_flexibility,
            total_sales,
            avg_rating,
            response_time_hours
        FROM sellers 
        WHERE trust_safety IS NOT NULL
        LIMIT :limit
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"limit": limit})
            sellers = []
            for row in result:
                sellers.append({
                    "seller_id": row[0],
                    "seller_name": row[1],
                    "persona_vector": {
                        "trust_safety": float(row[2]) if row[2] else 50.0,
                        "quality_condition": float(row[3]) if row[3] else 50.0,
                        "remote_transaction": float(row[4]) if row[4] else 50.0,
                        "activity_responsiveness": float(row[5]) if row[5] else 50.0,
                        "price_flexibility": float(row[6]) if row[6] else 50.0
                    },
                    "total_sales": int(row[7]) if row[7] else 0,
                    "avg_rating": float(row[8]) if row[8] else 0.0,
                    "response_time_hours": float(row[9]) if row[9] else 24.0
                })
            return sellers

    def get_products_by_sellers(self, seller_ids: List[str], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """특정 판매자들의 상품들 조회"""
        if not seller_ids:
            return []

        # 기본 쿼리
        query = """
        SELECT 
            p.product_id,
            p.seller_id,
            p.title,
            p.price,
            p.category,
            p.condition,
            p.location,
            p.description,
            p.created_at,
            p.view_count,
            p.like_count,
            s.seller_name,
            s.avg_rating as seller_rating
        FROM products p
        JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.seller_id IN :seller_ids
        """

        params = {"seller_ids": seller_ids}

        # 필터 적용
        if filters:
            if filters.get("price_min"):
                query += " AND p.price >= :price_min"
                params["price_min"] = filters["price_min"]
            if filters.get("price_max"):
                query += " AND p.price <= :price_max"
                params["price_max"] = filters["price_max"]
            if filters.get("category"):
                query += " AND p.category = :category"
                params["category"] = filters["category"]
            if filters.get("location"):
                query += " AND p.location LIKE :location"
                params["location"] = f"%{filters['location']}%"

        query += " ORDER BY p.created_at DESC"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            products = []
            for row in result:
                products.append({
                    "product_id": row[0],
                    "seller_id": row[1],
                    "title": row[2],
                    "price": float(row[3]),
                    "category": row[4],
                    "condition": row[5],
                    "location": row[6],
                    "description": row[7],
                    "created_at": row[8],
                    "view_count": int(row[9]) if row[9] else 0,
                    "like_count": int(row[10]) if row[10] else 0,
                    "seller_name": row[11],
                    "seller_rating": float(row[12]) if row[12] else 0.0
                })
            return products

    def get_mock_sellers(self) -> List[Dict[str, Any]]:
        """목업 판매자 데이터 (개발용)"""
        return [
            {
                "seller_id": "seller_1",
                "seller_name": "신뢰안전전문가",
                "persona_vector": {
                    "trust_safety": 95,
                    "quality_condition": 80,
                    "remote_transaction": 70,
                    "activity_responsiveness": 85,
                    "price_flexibility": 30
                },
                "total_sales": 150,
                "avg_rating": 4.8,
                "response_time_hours": 2.0
            },
            {
                "seller_id": "seller_2",
                "seller_name": "빠른배송왕",
                "persona_vector": {
                    "trust_safety": 75,
                    "quality_condition": 70,
                    "remote_transaction": 90,
                    "activity_responsiveness": 95,
                    "price_flexibility": 40
                },
                "total_sales": 200,
                "avg_rating": 4.6,
                "response_time_hours": 1.0
            },
            {
                "seller_id": "seller_3",
                "seller_name": "가격협상왕",
                "persona_vector": {
                    "trust_safety": 60,
                    "quality_condition": 60,
                    "remote_transaction": 50,
                    "activity_responsiveness": 70,
                    "price_flexibility": 90
                },
                "total_sales": 80,
                "avg_rating": 4.2,
                "response_time_hours": 4.0
            }
        ]

    def get_mock_products(self, seller_ids: List[str]) -> List[Dict[str, Any]]:
        """목업 상품 데이터 (개발용)"""
        mock_products = [
            {
                "product_id": "prod_1",
                "seller_id": "seller_1",
                "title": "아이폰 14 Pro Max 256GB 새상품",
                "price": 1200000,
                "category": "스마트폰",
                "condition": "새상품",
                "location": "서울 강남구",
                "description": "미개봉 새상품입니다. 안전결제 가능합니다.",
                "view_count": 150,
                "like_count": 25,
                "seller_name": "신뢰안전전문가",
                "seller_rating": 4.8
            },
            {
                "product_id": "prod_2",
                "seller_id": "seller_2",
                "title": "맥북 프로 16인치 M2 칩",
                "price": 2500000,
                "category": "노트북",
                "condition": "중고",
                "location": "서울 서초구",
                "description": "빠른배송 가능합니다. 상태 양호합니다.",
                "view_count": 200,
                "like_count": 40,
                "seller_name": "빠른배송왕",
                "seller_rating": 4.6
            },
            {
                "product_id": "prod_3",
                "seller_id": "seller_3",
                "title": "나이키 에어맥스 270 운동화",
                "price": 150000,
                "category": "신발",
                "condition": "거의새것",
                "location": "부산 해운대구",
                "description": "가격 협상 가능합니다. 직거래 선호합니다.",
                "view_count": 80,
                "like_count": 15,
                "seller_name": "가격협상왕",
                "seller_rating": 4.2
            }
        ]

        # seller_ids에 해당하는 상품만 필터링
        return [p for p in mock_products if p["seller_id"] in seller_ids]
