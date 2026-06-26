"""
데이터베이스 관리 모듈
SQLite를 사용하여 주가 데이터, 전고점 기록, 알림 발송 기록을 관리합니다.
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """데이터베이스 관리 클래스"""

    def __init__(self, db_path: str):
        """
        데이터베이스 초기화

        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 접근
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """데이터베이스 테이블 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 주가 데이터 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    close_price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """)

            # 전고점 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS all_time_highs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 알림 발송 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    triggered_at DATE NOT NULL,
                    alert_sent_at TIMESTAMP,
                    samsung_status TEXT,
                    email_sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date
                ON stock_prices(symbol, date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_all_time_highs_symbol
                ON all_time_highs(symbol, is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alert_history_triggered_at
                ON alert_history(triggered_at)
            """)

            logger.info("데이터베이스 초기화 완료")

    def save_price(self, symbol: str, price: float, date: date) -> bool:
        """
        주가 저장

        Args:
            symbol: 종목 코드
            price: 종가
            date: 날짜

        Returns:
            저장 성공 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO stock_prices (symbol, date, close_price)
                    VALUES (?, ?, ?)
                    """,
                    (symbol, date.isoformat(), price)
                )
                logger.info(f"주가 저장: {symbol} - {price} ({date})")
                return True
        except Exception as e:
            logger.error(f"주가 저장 실패: {e}")
            return False

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        최신 주가 조회

        Args:
            symbol: 종목 코드

        Returns:
            최신 종가 (없으면 None)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT close_price FROM stock_prices
                    WHERE symbol = ?
                    ORDER BY date DESC
                    LIMIT 1
                    """,
                    (symbol,)
                )
                row = cursor.fetchone()
                return row["close_price"] if row else None
        except Exception as e:
            logger.error(f"최신 주가 조회 실패: {e}")
            return None

    def get_all_time_high(self, symbol: str) -> Optional[float]:
        """
        전고점(52주 신고가) 조회

        Args:
            symbol: 종목 코드

        Returns:
            전고점 가격 (없으면 None)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT MAX(close_price) as max_price
                    FROM stock_prices
                    WHERE symbol = ?
                    AND date >= date('now', '-365 days')
                    """,
                    (symbol,)
                )
                row = cursor.fetchone()
                return row["max_price"] if row and row["max_price"] else None
        except Exception as e:
            logger.error(f"전고점 조회 실패: {e}")
            return None

    def get_active_all_time_high(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        활성 전고점 기록 조회

        Args:
            symbol: 종목 코드

        Returns:
            활성 전고점 정보 (없으면 None)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, symbol, price, date
                    FROM all_time_highs
                    WHERE symbol = ? AND is_active = 1
                    ORDER BY date DESC
                    LIMIT 1
                    """,
                    (symbol,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"활성 전고점 조회 실패: {e}")
            return None

    def save_all_time_high(self, symbol: str, price: float, date: date) -> bool:
        """
        새로운 전고점 기록 저장

        Args:
            symbol: 종목 코드
            price: 전고점 가격
            date: 발생일

        Returns:
            저장 성공 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 기존 활성 전고점 비활성화
                cursor.execute(
                    """
                    UPDATE all_time_highs
                    SET is_active = 0
                    WHERE symbol = ? AND is_active = 1
                    """,
                    (symbol,)
                )

                # 새로운 전고점 저장
                cursor.execute(
                    """
                    INSERT INTO all_time_highs (symbol, price, date)
                    VALUES (?, ?, ?)
                    """,
                    (symbol, price, date.isoformat())
                )

                logger.info(f"새로운 전고점 기록: {symbol} - {price} ({date})")
                return True
        except Exception as e:
            logger.error(f"전고점 기록 저장 실패: {e}")
            return False

    def create_alert_trigger(self, triggered_at: date) -> bool:
        """
        알림 트리거 생성 (SK하이닉스 전고점 돌파 시)

        Args:
            triggered_at: 트리거 발생일 (SK하이닉스 전고점일)

        Returns:
            생성 성공 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO alert_history (triggered_at, samsung_status)
                    VALUES (?, 'PENDING')
                    """,
                    (triggered_at.isoformat(),)
                )
                logger.info(f"알림 트리거 생성: {triggered_at}")
                return True
        except Exception as e:
            logger.error(f"알림 트리거 생성 실패: {e}")
            return False

    def get_active_alert_trigger(self) -> Optional[Dict[str, Any]]:
        """
        활성 알림 트리거 조회

        Returns:
            활성 트리거 정보 (없으면 None)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, triggered_at, samsung_status, email_sent
                    FROM alert_history
                    WHERE samsung_status NOT IN ('COMPLETED', 'ATH_REACHED')
                    AND email_sent = 0
                    ORDER BY triggered_at DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"활성 트리거 조회 실패: {e}")
            return None

    def mark_email_sent(self, trigger_id: int) -> bool:
        """
        이메일 발송 완료 표시

        Args:
            trigger_id: 트리거 ID

        Returns:
            업데이트 성공 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE alert_history
                    SET email_sent = 1,
                        alert_sent_at = CURRENT_TIMESTAMP,
                        samsung_status = 'ALERT_SENT'
                    WHERE id = ?
                    """,
                    (trigger_id,)
                )
                logger.info(f"이메일 발송 완료 표시: 트리거 ID {trigger_id}")
                return True
        except Exception as e:
            logger.error(f"이메일 발송 표시 실패: {e}")
            return False

    def mark_trigger_completed(self, trigger_id: int, reason: str = "ATH_REACHED") -> bool:
        """
        트리거 완료 표시 (삼성전자 전고점 갱신 등)

        Args:
            trigger_id: 트리거 ID
            reason: 완료 사유

        Returns:
            업데이트 성공 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE alert_history
                    SET samsung_status = ?
                    WHERE id = ?
                    """,
                    (reason, trigger_id)
                )
                logger.info(f"트리거 완료: ID {trigger_id} - {reason}")
                return True
        except Exception as e:
            logger.error(f"트리거 완료 표시 실패: {e}")
            return False

    def get_price_history(self, symbol: str, days: int = 365) -> List[Dict[str, Any]]:
        """
        주가 이력 조회

        Args:
            symbol: 종목 코드
            days: 조회 기간 (일)

        Returns:
            주가 이력 리스트
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT date, close_price
                    FROM stock_prices
                    WHERE symbol = ?
                    AND date >= date('now', '-' || ? || ' days')
                    ORDER BY date DESC
                    """,
                    (symbol, days)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"주가 이력 조회 실패: {e}")
            return []

    def check_samsung_ath_since(self, since_date: date) -> bool:
        """
        지정일 이후 삼성전자 전고점 갱신 여부 확인

        Args:
            since_date: 기준일

        Returns:
            전고점 갱신 여부
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 기준일 이후 삼성전자 전고점 기록 확인
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM all_time_highs
                    WHERE symbol = ?
                    AND date > ?
                    AND is_active = 1
                    """,
                    ("005930.KS", since_date.isoformat())
                )
                row = cursor.fetchone()
                return row["count"] > 0 if row else False
        except Exception as e:
            logger.error(f"삼성전자 전고점 확인 실패: {e}")
            return False
