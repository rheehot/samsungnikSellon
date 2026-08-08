"""
주가 데이터 수집 모듈
Yahoo Finance API를 사용하여 주가 데이터를 수집합니다.
"""

import yfinance as yf
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict
import time

logger = logging.getLogger(__name__)


class StockAPI:
    """주가 데이터 수집 클래스"""

    def __init__(self, retry_attempts: int = 3, retry_delay: int = 5):
        """
        API 클라이언트 초기화

        Args:
            retry_attempts: 재시도 횟수
            retry_delay: 재시도 대기 시간 (초)
        """
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """
        최신 주가 조회

        Args:
            symbol: 종목 코드 (예: "005930.KS")

        Returns:
            최신 종가 (실패 시 None)
        """
        for attempt in range(self.retry_attempts):
            try:
                ticker = yf.Ticker(symbol)
                # fast=True로 빠른 조회
                info = ticker.fast_info

                # yfinance FastInfo는 .get()이 snake_case를 인식 못 함 → 인덱싱 사용
                current_price = info["last_price"]
                if current_price:
                    logger.info(f"주가 수집 성공: {symbol} - {current_price}")
                    return current_price
                else:
                    logger.warning(f"주가 데이터 없음: {symbol}")
                    return None

            except Exception as e:
                logger.warning(f"주가 수집 실패 (시도 {attempt + 1}/{self.retry_attempts}): {symbol} - {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"주가 수집 최종 실패: {symbol}")
                    return None

        return None

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        종목 상세 정보 조회

        Args:
            symbol: 종목 코드

        Returns:
            종목 정보 딕셔너리
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "market": info.get("market", ""),
                "currency": info.get("currency", "KRW"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.error(f"종목 정보 조회 실패: {symbol} - {e}")
            return None

    def get_historical_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[date, float]:
        """
        과거 주가 데이터 조회

        Args:
            symbol: 종목 코드
            start_date: 시작일
            end_date: 종료일 (기본: 오늘)

        Returns:
            {날짜: 종가} 딕셔너리
        """
        if end_date is None:
            end_date = date.today()

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d")
            )

            prices = {}
            for dt, row in hist.iterrows():
                prices[dt.date()] = row["Close"]

            logger.info(f"과거 주가 수집: {symbol} - {len(prices)}일치 데이터")
            return prices

        except Exception as e:
            logger.error(f"과거 주가 수집 실패: {symbol} - {e}")
            return {}

    def get_latest_52_week_high(self, symbol: str) -> Optional[float]:
        """
        52주 신고가 조회

        Args:
            symbol: 종목 코드

        Returns:
            52주 신고가
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=365)

            prices = self.get_historical_prices(symbol, start_date, end_date)

            if prices:
                return max(prices.values())
            return None

        except Exception as e:
            logger.error(f"52주 신고가 조회 실패: {symbol} - {e}")
            return None


def test_api():
    """API 테스트 함수"""
    api = StockAPI()

    # 삼성전자 주가 조회
    samsung_price = api.get_stock_price("005930.KS")
    print(f"삼성전자 현재가: {samsung_price}")

    # SK하이닉스 주가 조회
    skhynix_price = api.get_stock_price("000660.KS")
    print(f"SK하이닉스 현재가: {skhynix_price}")

    # 종목 정보 조회
    info = api.get_stock_info("005930.KS")
    print(f"삼성전자 정보: {info}")


if __name__ == "__main__":
    test_api()
