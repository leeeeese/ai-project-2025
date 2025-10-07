"""
데이터베이스 연결 설정
MySQL과 PostgreSQL 연결을 관리합니다.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_mysql_url, get_postgres_url

# MySQL 엔진 (기존 데이터)
mysql_engine = create_engine(
    get_mysql_url(),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

# PostgreSQL 엔진 (State 저장)
postgres_engine = create_engine(
    get_postgres_url(),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

# 세션 팩토리
MySQLSession = sessionmaker(bind=mysql_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

# 베이스 클래스
MySQLBase = declarative_base()
PostgresBase = declarative_base()

# 메타데이터
mysql_metadata = MetaData(bind=mysql_engine)
postgres_metadata = MetaData(bind=postgres_engine)


def get_mysql_session():
    """MySQL 세션 반환"""
    return MySQLSession()


def get_postgres_session():
    """PostgreSQL 세션 반환"""
    return PostgresSession()


def init_databases():
    """데이터베이스 초기화"""
    try:
        # PostgreSQL에 LangGraph 체크포인트 테이블 생성
        postgres_engine.execute("""
            CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
                thread_id VARCHAR(255) PRIMARY KEY,
                checkpoint_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("PostgreSQL 데이터베이스 초기화 완료")
    except Exception as e:
        print(f"데이터베이스 초기화 오류: {e}")


def test_connections():
    """데이터베이스 연결 테스트"""
    try:
        # MySQL 연결 테스트
        with mysql_engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("MySQL 연결 성공")

        # PostgreSQL 연결 테스트
        with postgres_engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("PostgreSQL 연결 성공")

    except Exception as e:
        print(f"데이터베이스 연결 테스트 실패: {e}")
        raise
