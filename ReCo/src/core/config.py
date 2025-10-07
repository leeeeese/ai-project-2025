"""
설정 관리
환경변수와 애플리케이션 설정을 관리합니다.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션 설정
    app_name: str = "ReCo - 중고거래 추천 시스템"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # OpenAI 설정
    openai_api_key: str
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.1

    # MySQL 설정 (기존 데이터)
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "reco_data"

    # PostgreSQL 설정 (State 저장)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_database: str = "reco_state"

    # LangGraph 설정
    langgraph_checkpoint_dir: str = "./checkpoints"
    max_iterations: int = 10

    # 추천 시스템 설정
    max_recommendations: int = 20
    min_match_score: float = 0.3
    persona_confidence_threshold: float = 0.6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 인스턴스
settings = Settings()


def get_mysql_url() -> str:
    """MySQL 연결 URL 생성"""
    return f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"


def get_postgres_url() -> str:
    """PostgreSQL 연결 URL 생성"""
    return f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"


def get_langgraph_config() -> dict:
    """LangGraph 설정 반환"""
    return {
        "checkpointer": {
            "type": "postgres",
            "url": get_postgres_url(),
            "table_name": "langgraph_checkpoints"
        },
        "max_iterations": settings.max_iterations
    }
