"""
SQL 쿼리 생성 유틸리티
최종 점수 기반으로 SQL 쿼리를 생성합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import json


class SQLGenerator:
    """SQL 쿼리 생성기"""

    def __init__(self):
        self.base_query = """
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
            s.avg_rating as seller_rating,
            s.total_sales,
            s.response_time_hours,
            :final_score as recommendation_score
        FROM products p
        JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.product_id = :product_id
        """

    def generate_query(self, final_item_scores: List[Dict[str, Any]],
                       limit: int = 20) -> Dict[str, Any]:
        """최종 점수 기반 SQL 쿼리 생성"""
        if not final_item_scores:
            return self._generate_empty_query()

        # 상위 N개 상품 선택
        top_items = final_item_scores[:limit]

        # SQL 쿼리 생성
        query, params = self._build_sql_query(top_items)

        # 샘플링 플랜 생성
        sample_plan = self._generate_sampling_plan(top_items)

        return {
            "query": query,
            "parameters": params,
            "sample_plan": sample_plan,
            "total_items": len(top_items),
            "execution_hints": self._generate_execution_hints(top_items)
        }

    def _build_sql_query(self, items: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """SQL 쿼리와 파라미터 생성"""
        if not items:
            return self._generate_empty_query()

        # 상품 ID 리스트 생성
        product_ids = [item['product_id'] for item in items]
        product_id_placeholders = ', '.join(
            [f':product_id_{i}' for i in range(len(product_ids))])

        # SQL 쿼리 생성
        query = f"""
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
            s.avg_rating as seller_rating,
            s.total_sales,
            s.response_time_hours,
            CASE p.product_id
                {self._generate_case_statements(items)}
            END as recommendation_score
        FROM products p
        JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.product_id IN ({product_id_placeholders})
        ORDER BY recommendation_score DESC
        """

        # 파라미터 생성
        params = {}
        for i, item in enumerate(items):
            params[f'product_id_{i}'] = item['product_id']

        return query, params

    def _generate_case_statements(self, items: List[Dict[str, Any]]) -> str:
        """CASE 문 생성 (추천 점수 매핑)"""
        case_statements = []
        for item in items:
            case_statements.append(
                f"WHEN '{item['product_id']}' THEN {item['final_score']:.6f}")
        return '\n                '.join(case_statements)

    def _generate_sampling_plan(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """샘플링 플랜 생성"""
        if not items:
            return {"strategy": "empty", "samples": []}

        # 점수 분포 분석
        scores = [item['final_score'] for item in items]
        min_score = min(scores)
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # 샘플링 전략 결정
        if max_score - min_score < 0.1:
            strategy = "uniform"  # 점수가 비슷하면 균등 샘플링
        elif avg_score > 0.7:
            strategy = "top_heavy"  # 높은 점수면 상위 집중
        else:
            strategy = "weighted"  # 가중치 기반 샘플링

        # 샘플링 계획 생성
        sample_plan = {
            "strategy": strategy,
            "total_items": len(items),
            "score_range": {
                "min": min_score,
                "max": max_score,
                "avg": avg_score
            },
            "samples": self._generate_samples(items, strategy)
        }

        return sample_plan

    def _generate_samples(self, items: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
        """샘플 생성"""
        samples = []

        if strategy == "uniform":
            # 균등 샘플링
            step = max(1, len(items) // 10)  # 최대 10개 샘플
            for i in range(0, len(items), step):
                samples.append({
                    "rank": i + 1,
                    "product_id": items[i]['product_id'],
                    "title": items[i]['title'],
                    "score": items[i]['final_score'],
                    "sampling_reason": "uniform_distribution"
                })

        elif strategy == "top_heavy":
            # 상위 집중 샘플링
            top_count = min(5, len(items))
            for i in range(top_count):
                samples.append({
                    "rank": i + 1,
                    "product_id": items[i]['product_id'],
                    "title": items[i]['title'],
                    "score": items[i]['final_score'],
                    "sampling_reason": "top_performers"
                })

        else:  # weighted
            # 가중치 기반 샘플링
            for i, item in enumerate(items):
                if i < 3 or item['final_score'] > 0.8:  # 상위 3개 또는 높은 점수
                    samples.append({
                        "rank": i + 1,
                        "product_id": item['product_id'],
                        "title": item['title'],
                        "score": item['final_score'],
                        "sampling_reason": "high_score" if item['final_score'] > 0.8 else "top_rank"
                    })

        return samples

    def _generate_execution_hints(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """실행 힌트 생성"""
        if not items:
            return {"hints": [], "optimization": "none"}

        # 카테고리 분포
        categories = [item['category'] for item in items]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 판매자 분포
        sellers = [item['seller_id'] for item in items]
        seller_counts = {}
        for seller in sellers:
            seller_counts[seller] = seller_counts.get(seller, 0) + 1

        hints = []

        # 인덱스 힌트
        if len(set(categories)) > 1:
            hints.append("Consider index on products.category")
        if len(set(sellers)) > 1:
            hints.append("Consider index on products.seller_id")

        # 쿼리 최적화 힌트
        if len(items) > 10:
            hints.append("Consider LIMIT clause for better performance")

        return {
            "hints": hints,
            "optimization": "standard",
            "estimated_rows": len(items),
            "category_diversity": len(set(categories)),
            "seller_diversity": len(set(sellers))
        }

    def _generate_empty_query(self) -> Dict[str, Any]:
        """빈 결과용 쿼리 생성"""
        return {
            "query": "SELECT 'No recommendations available' as message",
            "parameters": {},
            "sample_plan": {"strategy": "empty", "samples": []},
            "total_items": 0,
            "execution_hints": {"hints": [], "optimization": "none"}
        }

    def generate_batch_queries(self, final_item_scores: List[Dict[str, Any]],
                               batch_size: int = 10) -> List[Dict[str, Any]]:
        """배치 쿼리 생성 (대량 데이터용)"""
        if not final_item_scores:
            return [self._generate_empty_query()]

        queries = []
        for i in range(0, len(final_item_scores), batch_size):
            batch = final_item_scores[i:i + batch_size]
            query_info = self.generate_query(batch, limit=len(batch))
            query_info["batch_number"] = i // batch_size + 1
            query_info["batch_size"] = len(batch)
            queries.append(query_info)

        return queries
